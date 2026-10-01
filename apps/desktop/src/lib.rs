mod tray;
mod fs_watcher;
mod encryption;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      
      // Initialize System Tray
      tray::create_tray(app.handle())?;
      
      // Spawn FS Watcher
      fs_watcher::start_watcher(app.handle().clone());
      
      // Spawn Backend sidecar
      if cfg!(debug_assertions) {
          // Development mode: spawn via uv
          let mut backend_child = std::process::Command::new("uv")
              .args(["run", "uvicorn", "helios.main:app", "--port", "8000"])
              .current_dir("../../services")
              .spawn()
              .expect("Failed to spawn backend process");
    
          app.on_window_event(move |_window, event| {
              if let tauri::WindowEvent::Destroyed = event {
                  let _ = backend_child.kill();
              }
          });
      } else {
          // Production mode: use sidecar via tauri-plugin-shell
          use tauri_plugin_shell::ShellExt;
          let sidecar_command = app.handle().shell().sidecar("bin/helios_backend").unwrap();
          let (mut rx, mut child) = sidecar_command.spawn().expect("Failed to spawn helios_backend sidecar");
          
          tauri::async_runtime::spawn(async move {
              while let Some(event) = rx.recv().await {
                  if let tauri_plugin_shell::process::CommandEvent::Stdout(line) = event {
                      println!("Backend: {}", String::from_utf8_lossy(&line));
                  } else if let tauri_plugin_shell::process::CommandEvent::Stderr(line) = event {
                      println!("Backend Error: {}", String::from_utf8_lossy(&line));
                  }
              }
          });
          
          app.on_window_event(move |_window, event| {
              if let tauri::WindowEvent::Destroyed = event {
                  let _ = child.kill();
              }
          });
      }
      
      Ok(())
    })
    .invoke_handler(tauri::generate_handler![encryption::encrypt_file])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
