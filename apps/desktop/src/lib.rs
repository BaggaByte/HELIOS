mod tray;

use std::sync::Mutex;
use tauri::Manager;
use std::net::TcpListener;
use tauri_plugin_shell::process::CommandChild;

// State to store the dynamic port so the frontend can retrieve it
struct BackendConfig {
    port: u16,
}

// State to store the child process so we can reliably kill it on app exit
struct BackendProcess {
    child: Mutex<Option<CommandChild>>,
}

// State for dev process (std::process::Child)
struct DevBackendProcess {
    child: Mutex<Option<std::process::Child>>,
}

#[tauri::command]
fn get_backend_port(config: tauri::State<'_, BackendConfig>) -> u16 {
    config.port
}

fn get_available_port() -> u16 {
    TcpListener::bind("127.0.0.1:0")
        .and_then(|listener| listener.local_addr())
        .map(|addr| addr.port())
        .unwrap_or(8000)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let port = get_available_port();
    
    let builder = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(
            tauri_plugin_log::Builder::default()
                .level(log::LevelFilter::Info)
                .build(),
        )
        .manage(BackendConfig { port })
        .manage(BackendProcess { child: Mutex::new(None) })
        .manage(DevBackendProcess { child: Mutex::new(None) })
        .invoke_handler(tauri::generate_handler![get_backend_port])
        .setup(move |app| {
            // Initialize System Tray
            if let Err(e) = tray::create_tray(app.handle()) {
                log::error!("Failed to create system tray: {}", e);
            }
            
            // Spawn Backend sidecar
            if cfg!(debug_assertions) {
                // Development mode: spawn via uv
                let backend_child = std::process::Command::new("uv")
                    .args(["run", "uvicorn", "helios.main:app", "--port", &port.to_string()])
                    .current_dir("../../services")
                    .spawn()
                    .expect("Failed to spawn backend process");
                
                let state: tauri::State<DevBackendProcess> = app.state();
                *state.child.lock().unwrap() = Some(backend_child);
            } else {
                // Production mode: use sidecar via tauri-plugin-shell
                use tauri_plugin_shell::ShellExt;
                match app.handle().shell().sidecar("bin/helios_backend") {
                    Ok(mut sidecar_command) => {
                        sidecar_command = sidecar_command.arg("--port").arg(port.to_string());
                        
                        match sidecar_command.spawn() {
                            Ok((mut rx, child)) => {
                                let state: tauri::State<BackendProcess> = app.state();
                                *state.child.lock().unwrap() = Some(child);
                                
                                // Read logs and route them to Tauri's log plugin
                                tauri::async_runtime::spawn(async move {
                                    while let Some(event) = rx.recv().await {
                                        if let tauri_plugin_shell::process::CommandEvent::Stdout(line) = event {
                                            log::info!("Backend: {}", String::from_utf8_lossy(&line));
                                        } else if let tauri_plugin_shell::process::CommandEvent::Stderr(line) = event {
                                            log::error!("Backend Error: {}", String::from_utf8_lossy(&line));
                                        }
                                    }
                                });
                            }
                            Err(e) => log::error!("Failed to spawn helios_backend sidecar: {}", e),
                        }
                    }
                    Err(e) => log::error!("Failed to initialize sidecar command: {}", e),
                }
            }
            
            Ok(())
        });

    let app = builder
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| {
        if let tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit = event {
            // Guarantee backend shutdown when the app fully exits (via tray or window close)
            if let Some(state) = app_handle.try_state::<BackendProcess>() {
                if let Some(child) = state.child.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
            if let Some(state) = app_handle.try_state::<DevBackendProcess>() {
                if let Some(mut child) = state.child.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
        }
    });
}
