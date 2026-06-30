/**
 * AITP plugin for OpenCode — AITP 1.0.0 v5 adapter
 *
 * Equivalent to the Claude Code hooks/session_start.py + hooks/compact.py harness.
 * Reads the canonical using-aitp.md from the AITP-Research-Protocol repo (same
 * source Claude uses) and injects it with OpenCode tool-name adaptation into
 * every chat session.
 *
 * Layers:
 *   Layer 1 — Gateway injection (experimental.chat.system.transform)
 *   Layer 2 — AITP v5 runtime skills
 *   Layer 3 — Progressive recording navigation
 *   Layer 4 — Typed v5 MCP tools and verification
 */

import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Canonical AITP repo and topic paths. These are template-filled by project
// installs and can be overridden for local plugin experiments.
const AITP_REPO_ROOT = process.env.AITP_REPO_ROOT || '{{REPO_ROOT}}';
const TOPICS_ROOT = process.env.AITP_TOPICS_ROOT || '{{TOPICS_ROOT}}';
const GATEWAY_SKILL = path.join(AITP_REPO_ROOT, 'deploy/templates/claude-code/using-aitp.md');
const RUNTIME_SKILL = path.join(AITP_REPO_ROOT, 'deploy/templates/claude-code/aitp-runtime.md');

// Skills search dir (where using-aitp/SKILL.md and aitp-runtime/SKILL.md live)
const resolveSkillsDir = () => {
  const candidates = [
    path.resolve(__dirname, '../../skills'),
    path.resolve(__dirname, '../skills'),
  ];
  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, 'using-aitp', 'SKILL.md'))) {
      return candidate;
    }
  }
  return candidates[0];
};

const extractAndStripFrontmatter = (content) => {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) return { frontmatter: {}, content };
  const frontmatterStr = match[1];
  const body = match[2];
  const frontmatter = {};
  for (const line of frontmatterStr.split('\n')) {
    const colonIdx = line.indexOf(':');
    if (colonIdx > 0) {
      const key = line.slice(0, colonIdx).trim();
      const value = line.slice(colonIdx + 1).trim().replace(/^["']|["']$/g, '');
      frontmatter[key] = value;
    }
  }
  return { frontmatter, content: body };
};

/**
 * Adapt Claude-Code-specific tool names to OpenCode equivalents:
 *   mcp__aitp__aitp_*  →  aitp_*
 *   AskUserQuestion     →  question  (OpenCode native tool)
 *   ToolSearch(...)     →  removed (OpenCode tools are always available)
 *   {{TOPICS_ROOT}}    →  actual path
 *   {{REPO_ROOT}}      →  actual path
 */
const adaptForOpenCode = (content) => {
  let adapted = content
    // Template variable substitution
    .replace(/\{\{TOPICS_ROOT\}\}/g, TOPICS_ROOT)
    .replace(/\{\{REPO_ROOT\}\}/g, AITP_REPO_ROOT)
    // MCP tool prefix: mcp__aitp__aitp_* or bare mcp__aitp__* → aitp_
    .replace(/mcp__aitp__(aitp_)?/g, 'aitp_')
    // Remove "BEFORE asking... load AskUserQuestion..." paragraph (OpenCode tools are always available)
    .replace(/\*\*BEFORE asking ANY question to the user, you MUST load the AskUserQuestion tool first:\*\*/g, '')
    // Remove inline ToolSearch reference (runtime skill has backtick-quoted one)
    .replace(/- BEFORE using AskUserQuestion, load it: `ToolSearch\([^)]+\)`[\r\n]+/g, '')
    // Remove ToolSearch code block (uses [\r\n]+ for Windows CRLF)
    .replace(/```[\r\n]+Call: ToolSearch\([^)]+\)[\r\n]+```[\r\n]+/g, '')
    .replace(/Then use it for ALL questions\. NEVER type options as plain text\./g,
      'Use the `question` tool for ALL questions. NEVER type options as plain text.')
    // AskUserQuestion → question (all occurrences — safe, only appears in the skill content)
    .replace(/AskUserQuestion/g, 'question')
    // multiSelect → multiple (OpenCode question tool uses "multiple" not "multiSelect")
    .replace(/"multiSelect"/g, '"multiple"')
    // python3 → python (Windows)
    .replace(/python3 /g, 'python ')
    // Fix hardcoded offline recording path
    .replace(/python hooks\/aitp_event\.py/g,
      `python ${AITP_REPO_ROOT}/hooks/aitp_event.py`);

  return adapted;
};

/**
 * Build the full context injection block — same structure as
 * session_start.py::_build_context_injection()
 */
const buildContextInjection = (gatewayContent, runtimeContent) => {
  const adaptedGateway = adaptForOpenCode(gatewayContent);

  const opencodeNote = [
    '',
    '**OpenCode Tool Mapping:**',
    '- AITP MCP tools are v5 typed tools under `aitp_v5_*`.',
    '- Legacy aliases are disabled by default and are never the execution contract.',
    '- Use OpenCode\'s `question` tool for all user interactions (same JSON schema as AskUserQuestion)',
    '- Use OpenCode\'s `skill` tool to load AITP v5 runtime skills',
    '- File operations: use native Read/Write/Edit tools; topic state changes: use MCP tools',
    '- Topics root: ' + TOPICS_ROOT,
    '',
  ].join('\n');

  return [
    '<EXTREMELY_IMPORTANT>',
    'You have AITP superpowers.',
    '',
    '**Below is the full content of your using-aitp skill with the AITP protocol.**',
    'For all other skills, use the skill tool.',
    '',
    adaptedGateway,
    opencodeNote,
    '</EXTREMELY_IMPORTANT>',
    '',
    `AITP Runtime: use aitp_v5_build_workspace_recovery_audit(base="${TOPICS_ROOT}") when placement is unclear, then aitp_v5_get_execution_brief(base="${TOPICS_ROOT}", session_id=<session-id>).`,
    `Topics root: ${TOPICS_ROOT}`,
    `AITP repo: ${AITP_REPO_ROOT}`,
  ].join('\n');
};

const getRuntimeInjection = (runtimeContent) => {
  if (!runtimeContent) return null;
  const adapted = adaptForOpenCode(runtimeContent);
  return [
    '<EXTREMELY_IMPORTANT>',
    '**AITP Runtime skill content (auto-injected):**',
    '',
    adapted,
    '</EXTREMELY_IMPORTANT>',
  ].join('\n');
};

const getBootstrapContent = () => {
  const gatewayExists = fs.existsSync(GATEWAY_SKILL);
  if (!gatewayExists) return null;

  const gatewayRaw = fs.readFileSync(GATEWAY_SKILL, 'utf8');
  const { content: gatewayContent } = extractAndStripFrontmatter(gatewayRaw);

  let runtimeContent = null;
  if (fs.existsSync(RUNTIME_SKILL)) {
    const runtimeRaw = fs.readFileSync(RUNTIME_SKILL, 'utf8');
    const { content: rc } = extractAndStripFrontmatter(runtimeRaw);
    runtimeContent = rc;
  }

  const context = buildContextInjection(gatewayContent, runtimeContent);
  return context;
};

export const AITPPlugin = async () => {
  const skillsDir = resolveSkillsDir();

  return {
    config: async (config) => {
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(skillsDir)) {
        config.skills.paths.push(skillsDir);
      }
    },

    'experimental.chat.system.transform': async (_input, output) => {
      const bootstrap = getBootstrapContent();
      if (bootstrap) {
        (output.system ||= []).push(bootstrap);
      }
    },
  };
};

export default AITPPlugin;
