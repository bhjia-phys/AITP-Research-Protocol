/**
 * AITP plugin for OpenCode - AITP 1.0.0 v5 adapter.
 *
 * This bootstrap registers the packaged AITP skills only. It does not inject
 * skill bodies, MEMORY.md, stage guidance, or research context into the system
 * prompt. Bounded recall is requested through aitp_v5_get_execution_brief or
 * aitp_v5_build_workspace_recovery_audit and delivered by the reviewed host
 * lifecycle integration.
 */

import path from 'node:path';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const resolveSkillsDir = () => {
  const candidates = [
    path.resolve(__dirname, '../../skills'),
    path.resolve(__dirname, '../skills'),
  ];
  for (const candidate of candidates) {
    if (existsSync(path.join(candidate, 'using-aitp', 'SKILL.md'))) {
      return candidate;
    }
  }
  return candidates[0];
};

export const AITP_ENTRYPOINTS = Object.freeze([
  'aitp_v5_get_execution_brief',
  'aitp_v5_build_workspace_recovery_audit',
]);

export const AITPPlugin = async () => {
  const skillsDir = resolveSkillsDir();

  return {
    config: async (config) => {
      config.skills ||= {};
      config.skills.paths ||= [];
      if (!config.skills.paths.includes(skillsDir)) {
        config.skills.paths.push(skillsDir);
      }
    },
  };
};

export default AITPPlugin;
