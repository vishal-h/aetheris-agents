import { Routes, Route, Navigate } from 'react-router-dom';
import { TopBar } from '@/components/shell/TopBar';
import { Sidebar } from '@/components/shell/Sidebar';
import { MainArea } from '@/components/shell/MainArea';
import { RightPanel } from '@/components/shell/RightPanel';
import { HarnessRoute } from '@/components/modules/harness/RunList';
import { OrchestratorView } from '@/components/modules/orchestrator/OrchestratorView';
import { DiffView } from '@/components/modules/harness/DiffView';
import { F2Operations, F2Viewer } from '@/components/modules/f2';
import { SettingsRoute } from '@/components/modules/settings/SettingsRoute';
import { CapabilityMatrixView } from '@/components/modules/harness/CapabilityMatrixView';
import { UsageView } from '@/components/modules/harness/UsageView';
import { CorpusOverview } from '@/components/modules/provenance/CorpusOverview';
import { ClassificationReview } from '@/components/modules/provenance/ClassificationReview';
import { MigrationStatus } from '@/components/modules/provenance/MigrationStatus';
import { ZipStatus } from '@/components/modules/provenance/ZipStatus';
import { useScanStatus } from '@/hooks/useScanStatus';

function App() {
  const { scanning, triggerScan } = useScanStatus();

  return (
    <div className="flex flex-col h-screen">
      {/* TopBar - fixed height */}
      <TopBar onSync={triggerScan} syncing={scanning} />

      {/* Main content area - flex row with Sidebar + content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar - fixed width */}
        <Sidebar />

        {/* Content area - flex row with MainArea + RightPanel */}
        <div className="flex flex-1 overflow-hidden">
          <Routes>
            {/* Root redirect to /harness */}
            <Route path="/" element={<Navigate to="/harness" replace />} />

            {/* Harness — agent run inspector */}
            <Route path="/harness" element={<HarnessRoute />} />

            {/* Diff — two-run comparison */}
            <Route path="/diff" element={
              <div className="flex flex-1 flex-col h-full bg-background overflow-y-auto">
                <DiffView />
              </div>
            } />

            {/* Capability matrix — agent/script catalogue */}
            <Route path="/capability-matrix" element={
              <div className="flex flex-1 flex-col h-full bg-background overflow-hidden">
                <CapabilityMatrixView />
              </div>
            } />

            {/* Usage — token & cost statistics */}
            <Route path="/usage" element={
              <div className="flex flex-1 flex-col h-full bg-background overflow-hidden">
                <UsageView />
              </div>
            } />

            {/* Orchestrator — natural language request + plan approval */}
            <Route path="/orchestrator" element={
              <div className="flex flex-1 flex-col h-full bg-background overflow-y-auto p-8">
                <OrchestratorView />
              </div>
            } />

            {/* F2 routes */}
            <Route path="/f2/operations" element={<MainArea tabs={F2Operations()} />} />
            <Route path="/f2/viewer"     element={<MainArea tabs={F2Viewer()} />} />

            {/* Provenance — all tabs in pipeline order */}
            <Route
              path="/provenance"
              element={
                <MainArea tabs={[
                  ...CorpusOverview(),
                  ...ClassificationReview(),
                  ...MigrationStatus(),
                  ...ZipStatus(),
                ]} />
              }
            />

            {/* Settings */}
            <Route path="/settings" element={<SettingsRoute />} />
          </Routes>

          {/* RightPanel - conditionally rendered based on context */}
          <RightPanel title="Details">
            <p className="text-sm text-muted-foreground">Panel content goes here</p>
          </RightPanel>
        </div>
      </div>
    </div>
  );
}

export default App;
