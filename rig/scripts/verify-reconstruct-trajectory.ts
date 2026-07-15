// Durable regression guard for the BL-005 trajectory reconstruction
// (`src/lib/reconstructTrajectory.ts`). Rig has no test runner, so this is a
// standalone Bun script over committed fixtures — no DB or network needed.
//
//   bun run rig/scripts/verify-reconstruct-trajectory.ts   (from repo root)
//   bun run scripts/verify-reconstruct-trajectory.ts       (from rig/)
//
// Exit 0 = all checks pass. The headline property (Test A) is byte-fidelity:
// events reconstructed from the SQLite shape (`harness_get_events`, payload as a
// JSON *string*) must equal the same run's `trajectory.json` (payload inlined as
// an object) field-for-field. A future refactor of TrajectoryView / the fork UX
// (BL-007) that silently breaks this fails here.
//
// Fixtures under scripts/fixtures/reconstruct/ are real harness output:
//   docbuilder-orch-iDGIIQ — 58-event completed run WITH a trajectory.json
//   run_YchSWw             — BL-003-swept run (failed, 3 events, no file)
import {
  reconstructTrajectory,
  reconstructedBanner,
  parseEventRow,
} from '../src/lib/reconstructTrajectory';

const DIR = `${import.meta.dir}/fixtures/reconstruct`;

let failures = 0;
function check(name: string, cond: boolean, detail = '') {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${detail ? '  — ' + detail : ''}`);
  if (!cond) failures++;
}
function deepEqual(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

// ── Test A: byte-fidelity vs the real trajectory.json ─────────────────────────
{
  const RID = 'docbuilder-orch-iDGIIQ';
  const rows = JSON.parse(await Bun.file(`${DIR}/${RID}.events.json`).text());
  const config = (await Bun.file(`${DIR}/${RID}.config.json`).text()).trim();
  const file = JSON.parse(await Bun.file(`${DIR}/${RID}.trajectory.json`).text());

  const recon = reconstructTrajectory(RID, null, config, rows);

  check('A: same event count as file', recon.events.length === file.events.length,
    `recon=${recon.events.length} file=${file.events.length}`);

  let mismatches = 0;
  for (let i = 0; i < file.events.length; i++) {
    const fe = file.events[i];
    const re = recon.events[i];
    const ok =
      re.id === fe.id &&
      re.run_id === fe.run_id &&
      re.seq === fe.seq &&
      re.step === fe.step &&
      re.event_type === fe.type &&       // file uses "type", recon normalises to "event_type"
      re.timestamp === fe.timestamp &&
      deepEqual(re.payload, fe.payload); // string (DB) → object must equal inlined object (file)
    if (!ok) {
      mismatches++;
      if (mismatches <= 3) console.log(`   mismatch @${i}: recon=${JSON.stringify(re).slice(0, 120)}`);
    }
  }
  check('A: every reconstructed event is byte-identical to the file', mismatches === 0,
    `${mismatches} mismatch(es) of ${file.events.length}`);

  check('A: meta.model matches file', recon.meta.model === file.meta.model,
    `recon=${recon.meta.model} file=${file.meta.model}`);
  check('A: meta.max_steps matches file', recon.meta.max_steps === file.meta.max_steps,
    `recon=${recon.meta.max_steps} file=${file.meta.max_steps}`);
  check('A: meta.tools matches file', deepEqual(recon.meta.tools, file.meta.tools),
    `recon=${JSON.stringify(recon.meta.tools)} file=${JSON.stringify(file.meta.tools)}`);
  check('A: meta.system_prompt matches file', recon.meta.system_prompt === file.meta.system_prompt);
}

// ── Test B: BL-003-swept terminal run (no trajectory.json) ────────────────────
{
  const RID = 'run_YchSWw';
  const rows = JSON.parse(await Bun.file(`${DIR}/${RID}.events.json`).text());
  const config = (await Bun.file(`${DIR}/${RID}.config.json`).text()).trim();
  const run = {
    run_id: RID, label: RID, status: 'failed', provider: 'stub', model: 'stub-v1',
    started_at: '2026-06-26T13:43:49.379427Z', finished_at: '2026-06-26T13:43:49.404423Z',
    step_count: 0, event_count: 3, last_event_at: null, total_cost_usd: null,
  };
  const recon = reconstructTrajectory(RID, run, config, rows);

  check('B: reconstructs 3 events for swept run', recon.events.length === 3,
    `got ${recon.events.length}`);
  check('B: banner reads "trajectory file unavailable …" for terminal run',
    reconstructedBanner(run.status) === 'trajectory file unavailable — reconstructed from events',
    reconstructedBanner(run.status));
  check('B: finished_at carried from terminal run row',
    recon.meta.finished_at === '2026-06-26T13:43:49.404423Z', recon.meta.finished_at);
  check('B: system_prompt derived from config_json',
    recon.meta.system_prompt === 'You are a test agent.', recon.meta.system_prompt);
  check('B: first event payload parsed into an object (not a string)',
    typeof recon.events[0].payload === 'object' && recon.events[0].payload !== null);
}

// ── Test C: synthetic running run — live banner + empty finished_at ───────────
{
  const RID = 'synthetic-live';
  const run = {
    run_id: RID, label: 'live one', status: 'running', provider: 'anthropic',
    model: 'claude-haiku-4-5', started_at: '2026-07-15T10:00:00Z', finished_at: null,
    step_count: 1, event_count: 2, last_event_at: null, total_cost_usd: null,
  };
  const rows = [
    { id: 'a', run_id: RID, step: 0, seq: 0, event_type: 'prompt_built',
      payload: '{"message_count":1}', timestamp: '2026-07-15T10:00:01Z' },
    { id: 'b', run_id: RID, step: 0, seq: 1, event_type: 'llm_called',
      payload: '{"model":"claude-haiku-4-5"}', timestamp: '2026-07-15T10:00:02Z' },
  ];
  const config = '{"mode":"record","max_steps":8,"tools":["run_command"]}';
  const recon = reconstructTrajectory(RID, run, config, rows);

  check('C: banner reads "live …" for running run',
    reconstructedBanner(run.status) === 'live — reconstructed from events',
    reconstructedBanner(run.status));
  check('C: finished_at is "" for a live run', recon.meta.finished_at === '',
    JSON.stringify(recon.meta.finished_at));
  check('C: step_count derived from distinct steps', recon.meta.step_count === 1,
    String(recon.meta.step_count));
  check('C: max_steps from config', recon.meta.max_steps === 8, String(recon.meta.max_steps));
  check('C: provider/model fall back cleanly', recon.meta.provider === 'anthropic');
}

// ── Test D: malformed payload never throws, preserved under _raw ──────────────
{
  const bad = parseEventRow({ id: 'x', run_id: 'r', step: 0, seq: 0,
    event_type: 'weird', payload: 'not-json{', timestamp: 't' });
  check('D: malformed payload preserved under _raw (no throw)',
    (bad.payload as Record<string, unknown>)._raw === 'not-json{');

  const empty = reconstructTrajectory('r', null, null, []);
  check('D: empty events + null config yields empty trajectory (no throw)',
    empty.events.length === 0 && empty.meta.tools.length === 0 && empty.meta.model === '');
}

console.log(`\n${failures === 0 ? '✅ ALL PASS' : `❌ ${failures} FAILURE(S)`}`);
process.exit(failures === 0 ? 0 : 1);
