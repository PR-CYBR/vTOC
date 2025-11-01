#!/usr/bin/env node

/**
 * Create the stage branch using GitHub API
 * 
 * This script creates the 'stage' branch from the current HEAD of the repository.
 * It requires a GITHUB_TOKEN environment variable with appropriate permissions.
 * 
 * Usage:
 *   GITHUB_TOKEN=<your-token> node scripts/create-stage-branch.js
 * 
 * Or run via the GitHub Actions workflow:
 *   .github/workflows/create-stage-branch.yml
 */

const https = require('https');

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const REPO_OWNER = 'PR-CYBR';
const REPO_NAME = 'vTOC';

if (!GITHUB_TOKEN) {
  console.error('Error: GITHUB_TOKEN environment variable is required');
  process.exit(1);
}

async function getCurrentSHA() {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.github.com',
      path: `/repos/${REPO_OWNER}/${REPO_NAME}/git/refs/heads/main`,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${GITHUB_TOKEN}`,
        'User-Agent': 'vTOC-stage-branch-creator',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          const response = JSON.parse(data);
          resolve(response.object.sha);
        } else {
          reject(new Error(`Failed to get main branch SHA: ${res.statusCode} ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

async function checkBranchExists() {
  return new Promise((resolve) => {
    const options = {
      hostname: 'api.github.com',
      path: `/repos/${REPO_OWNER}/${REPO_NAME}/git/refs/heads/stage`,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${GITHUB_TOKEN}`,
        'User-Agent': 'vTOC-stage-branch-creator',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve(res.statusCode === 200);
      });
    });

    req.on('error', () => resolve(false));
    req.end();
  });
}

async function createBranch(sha) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({
      ref: 'refs/heads/stage',
      sha: sha
    });

    const options = {
      hostname: 'api.github.com',
      path: `/repos/${REPO_OWNER}/${REPO_NAME}/git/refs`,
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${GITHUB_TOKEN}`,
        'User-Agent': 'vTOC-stage-branch-creator',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 201) {
          resolve(JSON.parse(data));
        } else {
          reject(new Error(`Failed to create branch: ${res.statusCode} ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.write(payload);
    req.end();
  });
}

async function main() {
  try {
    console.log('Checking if stage branch already exists...');
    const exists = await checkBranchExists();
    
    if (exists) {
      console.log('✓ Stage branch already exists');
      return;
    }

    console.log('Getting current main branch SHA...');
    const sha = await getCurrentSHA();
    console.log(`✓ Main branch SHA: ${sha}`);

    console.log('Creating stage branch...');
    await createBranch(sha);
    console.log('✓ Stage branch created successfully');
    console.log('');
    console.log('The stage branch is now available and the Stage CI Report workflow should work correctly.');
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

main();
