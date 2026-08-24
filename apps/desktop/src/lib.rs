mod tray;
mod fs_watcher;
mod encryption;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
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
      
      Ok(())
    })
    .invoke_handler(tauri::generate_handler![encryption::encrypt_file])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
