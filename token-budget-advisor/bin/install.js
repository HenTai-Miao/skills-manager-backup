#!/usr/bin/env node

const fs   = require('fs');
const path = require('path');
const os   = require('os');

const SKILL_NAME = 'token-budget-advisor';
const SKILL_FILES = ['SKILL.md', 'scripts', 'references', 'examples'];

// ─── Find install target ─────────────────────────────────────────────────────

function findProjectClaudeDir() {
  let dir = process.cwd();
  const root = path.parse(dir).root;
  while (dir !== root) {
    const candidate = path.join(dir, '.claude', 'skills');
    if (fs.existsSync(path.join(dir, '.claude'))) return candidate;
    dir = path.dirname(dir);
  }
  return null;
}

const projectSkillsDir = findProjectClaudeDir();
const globalSkillsDir  = path.join(os.homedir(), '.claude', 'skills');

let targetDir;
const args = process.argv.slice(2);

if (args.includes('--global') || args.includes('-g')) {
  targetDir = path.join(globalSkillsDir, SKILL_NAME);
} else if (projectSkillsDir) {
  targetDir = path.join(projectSkillsDir, SKILL_NAME);
} else {
  targetDir = path.join(globalSkillsDir, SKILL_NAME);
}

// ─── Copy helper ─────────────────────────────────────────────────────────────

function copyRecursive(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) copyRecursive(s, d);
    else fs.copyFileSync(s, d);
  }
}

// ─── Install ─────────────────────────────────────────────────────────────────

const sourceRoot = path.join(__dirname, '..');
const isUpdate   = fs.existsSync(targetDir);

console.log('');
console.log('  TBA — Token Budget Advisor for Claude Code');
console.log('  ───────────────────────────────────────────');
console.log(`  ${isUpdate ? 'Updating' : 'Installing'} → ${targetDir}`);
console.log('');

fs.mkdirSync(targetDir, { recursive: true });

for (const item of SKILL_FILES) {
  const src = path.join(sourceRoot, item);
  if (!fs.existsSync(src)) continue;
  const dest = path.join(targetDir, item);
  if (fs.statSync(src).isDirectory()) copyRecursive(src, dest);
  else fs.copyFileSync(src, dest);
}

console.log('  Done! Skill installed.');
console.log('');
console.log('  Claude will now offer depth levels before responding.');
console.log('  Trigger keywords: "tokens", "token budget", "profundidad",');
console.log('  "respuesta corta", "al 50%", "versión breve", ...');
console.log('');
console.log('  Flags:');
console.log('    --global / -g   Install to ~/.claude/skills/ (all projects)');
console.log('');
