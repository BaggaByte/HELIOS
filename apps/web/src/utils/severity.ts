/**
 * severity.ts
 *
 * Centralised severity badge styling for all security findings screens.
 * Always pair a severity badge with a text label — never rely on color alone.
 *
 * Token mapping (defined in index.css :root):
 *  critical → --severity-critical  #f85149  red
 *  high     → --severity-high      #e86300  orange (distinct from medium)
 *  medium   → --severity-medium    #c8a800  gold/yellow
 *  low      → --severity-low       #3fb950  green
 *  info/informational → --severity-info  #58a6ff  blue
 */

export type SeverityLevel =
  | 'critical'
  | 'high'
  | 'medium'
  | 'low'
  | 'info'
  | 'informational'
  | string;

/**
 * Returns Tailwind class strings for a severity badge.
 * Works with both UPPER and lower case severity labels.
 */
export function getSeverityClasses(severity: SeverityLevel): string {
  switch (severity.toLowerCase()) {
    case 'critical':
      return 'text-severity-critical bg-severity-critical/15 border-severity-critical/40';
    case 'high':
      return 'text-severity-high bg-severity-high/15 border-severity-high/40';
    case 'medium':
      return 'text-severity-medium bg-severity-medium/15 border-severity-medium/40';
    case 'low':
      return 'text-severity-low bg-severity-low/15 border-severity-low/40';
    case 'info':
    case 'informational':
    default:
      return 'text-severity-info bg-severity-info/15 border-severity-info/40';
  }
}

/**
 * Returns a short uppercase display label for a severity level.
 * Normalises "Informational" → "INFO" etc.
 */
export function getSeverityLabel(severity: SeverityLevel): string {
  const s = severity.toLowerCase();
  if (s === 'informational') return 'INFO';
  return s.toUpperCase();
}
