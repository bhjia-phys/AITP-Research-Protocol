/**
 * AITP plugin for OpenCode
 *
 * Injects the using-aitp bootstrap and registers the local AITP skills path.
 */

import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

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

const getBootstrapContent = () => {
  const skillsDir = resolveSkillsDir();
  const skillPath = path.join(skillsDir, 'using-aitp', 'SKILL.md');
  if (!fs.existsSync(skillPath)) return null;

  const fullContent = fs.readFileSync(skillPath, 'utf8');
  const { content } = extractAndStripFrontmatter(fullContent);
  const toolMapping = `**Tool Mapping for OpenCode:**\n- \`TodoWrite\` -> \`todowrite\`\n- \`Skill\` tool -> OpenCode's native \`skill\` tool\n- File operations and shell calls -> native OpenCode tools\n\n**AITP skills location:**\n\`${skillsDir}\``;

  return `<EXTREMELY_IMPORTANT>\nYou are in an AITP-enabled OpenCode session.\n\n**IMPORTANT: The using-aitp skill content is included below and is already loaded. Do not load using-aitp again.**\n\n${content}\n\n${toolMapping}\n</EXTREMELY_IMPORTANT>`;
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
    }
  };
};

export default AITPPlugin;
