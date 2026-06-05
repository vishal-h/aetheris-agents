import type { AgentConfigEntry } from '@/hooks/types';

export const AGENT_CONFIG_DEFS: Omit<AgentConfigEntry, 'value'>[] = [
  // Harness
  { key: 'AETHERIS_MODEL',      label: 'Default model',     group: 'Harness',      masked: false },
  { key: 'AETHERIS_PROVIDER',   label: 'Default provider',  group: 'Harness',      masked: false },

  // Anthropic
  { key: 'ANTHROPIC_API_KEY',   label: 'API key',           group: 'Anthropic',    masked: true  },

  // SMTP
  { key: 'SMTP_HOST',           label: 'Host',              group: 'SMTP',         masked: false },
  { key: 'SMTP_PORT',           label: 'Port',              group: 'SMTP',         masked: false },
  { key: 'SMTP_USER',           label: 'Username',          group: 'SMTP',         masked: false },
  { key: 'SMTP_PASSWORD',       label: 'Password',          group: 'SMTP',         masked: true  },
  { key: 'SMTP_FROM',           label: 'From address',      group: 'SMTP',         masked: false },
  { key: 'SMTP_TO',             label: 'To address',        group: 'SMTP',         masked: false },

  // Google Drive
  { key: 'GOOGLE_CREDENTIALS',  label: 'Credentials JSON',  group: 'Google Drive', masked: true  },

  // Provenance
  { key: 'PROVENANCE_NAS_PATH', label: 'NAS archive path',  group: 'Provenance',   masked: false },
];
