use notify::{Config, Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
use std::path::Path;
use std::sync::mpsc::channel;
use tauri::{AppHandle, Emitter};

pub fn start_watcher(app: AppHandle) {
    std::thread::spawn(move || {
        let (tx, rx) = channel();

        // Create a watcher object, delivering debounced events.
        // The notification back-channel is connected to tx.
        let mut watcher = match RecommendedWatcher::new(tx, Config::default()) {
            Ok(w) => w,
            Err(e) => {
                log::error!("Failed to initialize FS watcher: {}", e);
                return;
            }
        };

        // Determine dropzone path (e.g., ~/.helios_storage/dropzone)
        let home_dir = dirs::home_dir().unwrap_or_else(|| Path::new(".").to_path_buf());
        let dropzone = home_dir.join(".helios_storage").join("dropzone");
        
        // Ensure directory exists
        let _ = std::fs::create_dir_all(&dropzone);

        // Add a path to be watched.
        if let Err(e) = watcher.watch(&dropzone, RecursiveMode::NonRecursive) {
            log::error!("Failed to watch dropzone {}: {}", dropzone.display(), e);
            return;
        }

        log::info!("Watching for new evidence in: {}", dropzone.display());

        // Process events
        for res in rx {
            match res {
                Ok(Event { kind: EventKind::Create(_), paths, .. }) => {
                    for path in paths {
                        log::info!("New file detected: {}", path.display());
                        
                        // Emit event to frontend
                        let _ = app.emit("file-dropped", path.to_string_lossy().to_string());
                    }
                }
                Ok(_) => {}
                Err(e) => log::error!("watch error: {:?}", e),
            }
        }
    });
}
