import { Module } from './types';

// Harness — Aetheris agent run inspector
const harnessModule: Module = {
  id: 'harness',
  label: 'Harness',
  icon: 'Activity',
  sections: [
    { id: 'harness-runs',      label: 'Runs',   icon: 'Activity',    path: '/harness'           },
    { id: 'diff',              label: 'Diff',   icon: 'GitCompare',  path: '/diff'              },
    { id: 'capability-matrix', label: 'Agents', icon: 'Library',     path: '/capability-matrix' },
    { id: 'usage',             label: 'Usage',  icon: 'TrendingUp',  path: '/usage'             },
  ],
};

// F2 - File & Folder module
const f2Module: Module = {
  id: 'f2',
  label: 'F2',
  icon: 'FolderSearch',
  sections: [
    {
      id: 'f2-operations',
      label: 'Operations',
      icon: 'ScanSearch',
      path: '/f2/operations',
    },
    {
      id: 'f2-viewer',
      label: 'Viewer',
      icon: 'LayoutTree',
      path: '/f2/viewer',
    },
  ],
};

// Provenance - corpus dashboard (single route, all tabs combined)
const provenanceModule: Module = {
  id: 'provenance',
  label: 'Provenance',
  icon: 'LayoutDashboard',
  sections: [
    {
      id: 'provenance',
      label: 'Dashboard',
      icon: 'LayoutDashboard',
      path: '/provenance',
    },
  ],
};

// Orchestrator — natural language request + plan approval workflow
const orchestratorModule: Module = {
  id: 'orchestrator',
  label: 'Orchestrator',
  icon: 'Sparkles',
  sections: [
    { id: 'orchestrator', label: 'Orchestrator', icon: 'Sparkles', path: '/orchestrator' },
  ],
};

// Tools — script browser and runner
const toolsModule: Module = {
  id: 'tools',
  label: 'Tools',
  icon: 'Wrench',
  sections: [
    { id: 'tools', label: 'Tools', icon: 'Wrench', path: '/tools' },
  ],
};

// Playground — Run Composer panel
const playgroundModule: Module = {
  id: 'playground',
  label: 'Playground',
  icon: 'FlaskConical',
  sections: [
    { id: 'playground', label: 'Composer', icon: 'FlaskConical', path: '/playground' },
  ],
};

// Module registry - add new modules here
export const modules: Module[] = [
  harnessModule,
  orchestratorModule,
  toolsModule,
  playgroundModule,
  f2Module,
  provenanceModule,
];
