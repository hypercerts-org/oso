import { BatchEventRecorder, TimeoutFlusher } from "../recorder/recorder.js";
import { BaseScheduler, Config } from "./types.js";
import {
  TimeSeriesCacheManager,
  TimeSeriesCacheWrapper,
} from "../cacher/time-series.js";
import { CommonArgs } from "../utils/api.js";
import { DateTime } from "luxon";
import { EventPointerManager } from "./pointers.js";
import { FundingEventsCollector } from "../actions/dune/funding-event-collector.js";
import { FundingEventsClient } from "../actions/dune/funding-events/client.js";
import { DuneClient } from "@cowprotocol/ts-dune-client";
import {
  DUNE_API_KEY,
  GITHUB_TOKEN,
  GITHUB_WORKERS_OWNER,
  GITHUB_WORKERS_REF,
  GITHUB_WORKERS_REPO,
  GITHUB_WORKERS_WORKFLOW_ID,
} from "../config.js";
import { ArtifactNamespace, ArtifactType } from "../db/orm-entities.js";
import { EventPointerRepository, EventRepository } from "../db/events.js";
import { ArtifactRepository } from "../db/artifacts.js";
import { AppDataSource } from "../db/data-source.js";
import { ProjectRepository } from "../db/project.js";
import { Octokit } from "octokit";
import { throttling } from "@octokit/plugin-throttling";
import { GithubCommitCollector } from "../actions/github/fetch/commits.js";
import { GithubIssueCollector } from "../actions/github/fetch/pull-requests.js";
import { GithubFollowingCollector } from "../actions/github/fetch/repo-followers.js";
import { DailyContractUsageCollector } from "../actions/dune/index.js";
import { DailyContractUsageClient } from "../actions/dune/daily-contract-usage/client.js";
import path from "path";
import { GithubWorkerSpawner } from "./github.js";
import { JobExecutionRepository, JobsRepository } from "../db/jobs.js";

export type SchedulerArgs = CommonArgs & {
  skipExisting?: boolean;
  batchSize: number;
};

export type SchedulerManualArgs = SchedulerArgs & {
  collector: string;
  startDate: DateTime;
  endDate: DateTime;
};

export type SchedulerWorkerArgs = SchedulerArgs & {
  group: string;
};

export type SchedulerQueueAllArgs = SchedulerArgs & {
  baseDate: DateTime;
};

export type SchedulerQueueJobArgs = SchedulerArgs & {
  collector: string;
  baseDate: DateTime;
  startDate: DateTime;
  endDate: DateTime;
};

// Entrypoint for the scheduler. Currently not where it should be but this is quick.
export async function configure(args: SchedulerArgs) {
  const flusher = new TimeoutFlusher(10000);
  const recorder = new BatchEventRecorder(
    EventRepository,
    ArtifactRepository,
    flusher,
  );
  const cacheManager = new TimeSeriesCacheManager(args.cacheDir);
  const cache = new TimeSeriesCacheWrapper(cacheManager);

  const AppOctoKit = Octokit.plugin(throttling);
  const gh = new AppOctoKit({
    auth: GITHUB_TOKEN,
    throttle: {
      onRateLimit: (retryAfter, options, octokit, retryCount) => {
        const opts = options as {
          method: string;
          url: string;
        };
        octokit.log.warn(
          `Request quota exhausted for request ${opts.method} ${opts.url}`,
        );
        // Retry up to 50 times (that should hopefully be more than enough)
        if (retryCount < 50) {
          octokit.log.info(`Retrying after ${retryAfter} seconds!`);
          return true;
        }
      },
      onSecondaryRateLimit: (retryAfter, options, octokit, retryCount) => {
        const opts = options as {
          method: string;
          url: string;
        };
        octokit.log.warn(
          `Secondary rate limit detected for ${opts.method} ${opts.url}`,
        );
        if (retryCount < 3) {
          octokit.log.info(`Retrying after ${retryAfter} seconds!`);
          return true;
        } else {
          octokit.log.info(`Failing now`);
        }
      },
    },
  });

  const config = new Config();
  const eventPointerManager = new EventPointerManager(
    AppDataSource,
    EventPointerRepository,
    {
      batchSize: args.batchSize,
    },
  );

  const spawner = new GithubWorkerSpawner(gh, {
    owner: GITHUB_WORKERS_OWNER,
    repo: GITHUB_WORKERS_REPO,
    ref: GITHUB_WORKERS_REF,
    workflowId: GITHUB_WORKERS_WORKFLOW_ID,
  });

  const scheduler = new BaseScheduler(
    args.runDir,
    recorder,
    config,
    eventPointerManager,
    cache,
    spawner,
    JobsRepository,
    JobExecutionRepository,
  );
  const dune = new DuneClient(DUNE_API_KEY);

  scheduler.registerCollector({
    create: async (_config, recorder, cache) => {
      const client = new FundingEventsClient(dune);

      const collector = new FundingEventsCollector(
        client,
        ProjectRepository,
        recorder,
        cache,
      );
      return collector;
    },
    name: "funding-events",
    description: "gathers funding events",
    group: "dune",
    schedule: "weekly",
    artifactScope: [ArtifactNamespace.OPTIMISM, ArtifactNamespace.ETHEREUM],
    artifactTypeScope: [
      ArtifactType.EOA_ADDRESS,
      ArtifactType.SAFE_ADDRESS,
      ArtifactType.CONTRACT_ADDRESS,
    ],
  });

  scheduler.registerCollector({
    create: async (_config, recorder, cache) => {
      const collector = new GithubCommitCollector(
        ProjectRepository,
        gh,
        recorder,
        cache,
      );
      return collector;
    },
    name: "github-commits",
    description: "Collects github commits",
    group: "github",
    schedule: "daily",
    artifactScope: [ArtifactNamespace.GITHUB],
    artifactTypeScope: [
      ArtifactType.GITHUB_USER,
      ArtifactType.GIT_EMAIL,
      ArtifactType.GIT_NAME,
      ArtifactType.GIT_REPOSITORY,
    ],
  });

  scheduler.registerCollector({
    create: async (_config, recorder, cache) => {
      const collector = new GithubIssueCollector(
        ProjectRepository,
        recorder,
        cache,
      );
      return collector;
    },
    name: "github-issues",
    description: "Collects github pull requests and issues",
    group: "github",
    schedule: "daily",
    artifactScope: [ArtifactNamespace.GITHUB],
    artifactTypeScope: [
      ArtifactType.GITHUB_USER,
      ArtifactType.GIT_EMAIL,
      ArtifactType.GIT_NAME,
      ArtifactType.GIT_REPOSITORY,
    ],
  });

  scheduler.registerCollector({
    create: async (_config, recorder, cache) => {
      const collector = new GithubFollowingCollector(
        ProjectRepository,
        recorder,
        cache,
      );
      return collector;
    },
    name: "github-followers",
    description: "Collects github pull requests and issues",
    group: "github",
    schedule: "weekly",
    artifactScope: [ArtifactNamespace.GITHUB],
    artifactTypeScope: [
      ArtifactType.GITHUB_ORG,
      ArtifactType.GITHUB_USER,
      ArtifactType.GIT_EMAIL,
      ArtifactType.GIT_NAME,
      ArtifactType.GIT_REPOSITORY,
    ],
  });

  scheduler.registerCollector({
    create: async (_config, recorder, cache) => {
      const client = new DailyContractUsageClient(dune);
      const collector = new DailyContractUsageCollector(
        client,
        ArtifactRepository,
        recorder,
        cache,
        {
          knownUserAddressesSeedPath: path.join(
            args.cacheDir,
            "known-user-addresses-seed.json",
          ),
        },
      );
      return collector;
    },
    name: "dune-daily-contract-usage",
    description: "Collects github pull requests and issues",
    group: "dune",
    schedule: "weekly",
    artifactScope: [ArtifactNamespace.OPTIMISM],
    artifactTypeScope: [
      ArtifactType.CONTRACT_ADDRESS,
      ArtifactType.EOA_ADDRESS,
      ArtifactType.SAFE_ADDRESS,
    ],
  });

  return scheduler;
}
