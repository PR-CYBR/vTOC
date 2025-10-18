const DEFAULT_BASE_BRANCH = 'main';
const DEFAULT_HEAD_BRANCH = 'prod';

module.exports = async function upsertProdSyncPr({ github, context, core }) {
  const owner = context.repo.owner;
  const repo = context.repo.repo;
  const base = DEFAULT_BASE_BRANCH;
  const head = DEFAULT_HEAD_BRANCH;

  core.info(`Ensuring a synchronization pull request exists for ${head} → ${base}.`);

  const { data: existing } = await github.rest.pulls.list({
    owner,
    repo,
    state: 'open',
    base,
    head: `${owner}:${head}`,
    per_page: 1,
  });

  if (existing.length > 0) {
    core.info(`Sync PR already open: ${existing[0].html_url}`);
    return existing[0];
  }

  const title = 'Sync prod into main';
  const body = [
    'Automated synchronization PR to fast-forward `main` with the latest production release.',
    '',
    '- Source branch: `prod`',
    '- Target branch: `main`',
    '',
    'This PR was created by the Fly deploy workflow after a successful health check.',
  ].join('\n');

  try {
    const { data: pr } = await github.rest.pulls.create({
      owner,
      repo,
      base,
      head,
      title,
      body,
      maintainer_can_modify: true,
      draft: false,
    });
    core.info(`Created synchronization PR: ${pr.html_url}`);
    return pr;
  } catch (error) {
    if (error.status === 422) {
      core.info('No differences between prod and main; no PR created.');
      return null;
    }
    throw error;
  }
};
