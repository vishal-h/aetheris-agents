import type { AgentConfigEntry } from '@/hooks/types';

export const AGENT_CONFIG_DEFS: Omit<AgentConfigEntry, 'value'>[] = [
  // Harness
  { key: 'AETHERIS_MODEL',      label: 'Default model',     group: 'Harness',
    masked: false, placeholder: 'claude-haiku-4-5-20251001' },
  { key: 'AETHERIS_PROVIDER',   label: 'Default provider',  group: 'Harness',
    masked: false, placeholder: 'anthropic' },

  // Anthropic
  { key: 'ANTHROPIC_API_KEY',   label: 'API key',           group: 'Anthropic',
    masked: true,  placeholder: 'sk-ant-...' },

  // SMTP
  { key: 'SMTP_HOST',           label: 'Host',              group: 'SMTP',
    masked: false, placeholder: 'smtp.gmail.com' },
  { key: 'SMTP_PORT',           label: 'Port',              group: 'SMTP',
    masked: false, placeholder: '587' },
  { key: 'SMTP_USER',           label: 'Username',          group: 'SMTP',
    masked: false, placeholder: 'sender@example.com' },
  { key: 'SMTP_PASSWORD',       label: 'Password',          group: 'SMTP',
    masked: true,  placeholder: 'app password (not your login password)' },
  { key: 'SMTP_FROM',           label: 'From address',      group: 'SMTP',
    masked: false, placeholder: 'payroll@example.com' },
  { key: 'SMTP_TO',             label: 'To address',        group: 'SMTP',
    masked: false, placeholder: 'payroll@example.com' },

  // Google Drive
  { key: 'GOOGLE_CREDENTIALS',  label: 'Credentials JSON',  group: 'Google Drive',
    masked: true,  placeholder: '{"type":"service_account",...}' },

  // Provenance
  { key: 'PROVENANCE_NAS_PATH', label: 'NAS archive path',  group: 'Provenance',
    masked: false, placeholder: '/mnt/nas/archive' },
];
