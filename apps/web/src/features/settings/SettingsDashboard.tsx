import { Settings as SettingsIcon } from 'lucide-react';

export function SettingsDashboard() {
  return (
    <div className="flex flex-col h-full bg-surface-primary p-6">
      <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border-default/50">
        <div className="w-10 h-10 rounded-lg bg-surface-secondary flex items-center justify-center border border-border-default shadow-md">
          <SettingsIcon size={24} className="text-gray-300" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-100 tracking-tight">Settings</h1>
          <p className="text-sm text-gray-400 mt-1">Configure HELIOS preferences and system options.</p>
        </div>
      </div>
      
      <div className="flex-1 flex flex-col items-center justify-center text-gray-400 animate-in fade-in duration-500">
        <SettingsIcon size={48} className="text-border-default mb-4 opacity-50" />
        <h3 className="text-xl font-semibold text-gray-300 mb-2">Settings Coming Soon</h3>
        <p className="text-sm text-gray-500 max-w-md text-center">
          The settings panel is currently under development. Soon you will be able to configure AI models, system integrations, and application preferences here.
        </p>
      </div>
    </div>
  );
}
