import { Module } from './types';

// Harness — Aetheris agent run inspector
const harnessModule: Module = {
  id: 'harness',
  label: 'Harness',
  icon: 'Activity',
  sections: [
    {
      id: 'harness-runs',
      label: 'Runs',
      icon: 'Activity',
      path: '/harness',
    },
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

// Module registry - add new modules here
export const modules: Module[] = [harnessModule, f2Module, provenanceModule];
