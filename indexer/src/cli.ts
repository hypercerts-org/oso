#!/usr/bin/env node
import yargs from "yargs";
import { DateTime } from "luxon";
import { hideBin } from "yargs/helpers";
import { RunAutocrawlArgs, runAutocrawl } from "./actions/autocrawl.js";
import { handleError } from "./utils/error.js";
//import { EventSourceFunction } from "./utils/api.js";
//import { NpmDownloadsArgs, NpmDownloadsInterface } from "./events/npm.js";
import {
  ImportOssDirectoryArgs,
  importOssDirectory,
} from "./actions/oss-directory.js";
import { AppDataSource } from "./db/data-source.js";
// import {
//   importDailyContractUsage,
// } from "./actions/dune/index.js";
// import { LoadCommits, loadCommits } from "./actions/github/fetch/commits.js";
// import {
//   LoadRepositoryFollowers,
//   loadRepositoryFollowers,
// } from "./actions/github/fetch/repo-followers.js";
// import {
//   LoadPullRequests,
//   loadPullRequests,
// } from "./actions/github/fetch/pull-requests.js";
import {
  SchedulerArgs,
  SchedulerManualArgs,
  SchedulerQueueAllArgs,
  SchedulerQueueJobArgs,
  SchedulerWorkerArgs,
  configure,
} from "./scheduler/index.js";

//const callLibrary = async <Args>(
//  func: EventSourceFunction<Args>,
//  args: Args,
//): Promise<void> => {
// TODO: handle ApiReturnType properly and generically here
//  const result = await func(args);
//  console.log(result);
//};

/**
 * When adding a new fetcher, please remember to add it to both this registry and yargs
 */
export const FETCHER_REGISTRY = [
  //NpmDownloadsInterface,
];
yargs(hideBin(process.argv))
  .middleware(async () => {
    // Initialize the database
    await AppDataSource.initialize();
  })
  .option("yes", {
    type: "boolean",
    describe: "Automatic yes to all prompts",
    default: false,
  })
  .option("autocrawl", {
    type: "boolean",
    describe: "Mark the query for auto-crawling",
    default: false,
  })
  .option("cache-dir", {
    type: "string",
    describe: "sets the path to the cache directory",
    default: "/tmp/oso",
  })
  .command<ImportOssDirectoryArgs>(
    "importOssDirectory",
    "Import projects and collections from 'oss-directory'",
    (yags) => {
      yags.option("skipExisting", { type: "boolean" });
    },
    (argv) => handleError(importOssDirectory(argv)),
  )
  // .command<ImportDailyContractUsage>(
  //   "importDailyContractUsage",
  //   "Manually import contract usage statistics from dune",
  //   (yags) => {
  //     yags
  //       .option("skipExisting", { type: "boolean" })
  //       .option("interval", { type: "number" })
  //       .option("base-date", { type: "string", default: "" })
  //       .coerce("base-date", (arg) => {
  //         if (arg === "") {
  //           return DateTime.now();
  //         }
  //         return DateTime.fromISO(arg);
  //       });
  //   },
  //   (argv) => handleError(importDailyContractUsage(argv)),
  // )
  // .command<LoadCommits>(
  //   "loadCommits",
  //   "Manually import commits",
  //   (yags) => {
  //     yags.option("skipExisting", { type: "boolean" });
  //   },
  //   (argv) => handleError(loadCommits(argv)),
  // )
  // .command<LoadRepositoryFollowers>(
  //   "loadRepositoryFollowers",
  //   "Manually import commits",
  //   (yags) => {
  //     yags.option("skipExisting", { type: "boolean" });
  //   },
  //   (argv) => handleError(loadRepositoryFollowers(argv)),
  // )
  // .command<LoadPullRequests>(
  //   "loadPullRequests",
  //   "Manually import pull requests",
  //   (yags) => {
  //     yags.option("skipExisting", { type: "boolean" });
  //   },
  //   (argv) => handleError(loadPullRequests(argv)),
  // )
  .command<RunAutocrawlArgs>(
    "runAutocrawl",
    "Iterate over EventSourcePointer table and update all data marked for autocrawl",
    (yags) => {
      yags;
    },
    (argv) => handleError(runAutocrawl(argv)),
  )
  // .command<NpmDownloadsArgs>(
  //   NpmDownloadsInterface.command,
  //   "Fetch NPM downloads",
  //   (yags) => {
  //     yags
  //       .option("name", {
  //         type: "string",
  //         describe: "Package name",
  //       })
  //       .demandOption(["name"]);
  //   },
  //   (argv) => handleError(callLibrary(NpmDownloadsInterface.func, argv)),
  // )
  .command<SchedulerArgs>(
    "scheduler <subcommand>",
    "scheduler commands",
    (yags) => {
      const dateConverter = (input: string) => {
        const date = DateTime.fromISO(input).toUTC();
        if (!date.isValid) {
          throw new Error(`input "${input}" is not a valid date`);
        }
        return date;
      };
      yags
        .command<SchedulerManualArgs>(
          "manual",
          "manually execute a scheduler run",
          (yags) => {
            yags
              .positional("collector", {
                describe: "the name of the collector to execute",
              })
              .option("start-date", {
                type: "string",
                describe: "start-date for the manual run",
              })
              .coerce("start-date", dateConverter)
              .option("end-date", {
                type: "string",
                describe: "start-date for the manual run",
              })
              .coerce("end-date", dateConverter)
              .demandOption(["start-date", "end-date"]);
          },
          async (args) => {
            const scheduler = await configure(args);

            await scheduler.executeForRange(args.collector, {
              startDate: args.startDate,
              endDate: args.endDate,
            });
          },
        )
        .command<SchedulerWorkerArgs>(
          "worker <group>",
          "run the worker",
          (yags) => {
            yags.positional("group", {
              describe: "the group to execute",
              type: "string",
            });
          },
          async (args) => {
            const scheduler = await configure(args);
            const errors = await scheduler.runWorker(args.group);
            if (errors.length > 0) {
              process.exit(1);
            }
          },
        )
        .command<SchedulerQueueAllArgs>(
          "queue [base-date]",
          "schedule workers into the queue",
          (yags) => {
            yags
              .positional("base-date", {
                describe: "the date to start scheduling from",
                type: "string",
              })
              .coerce("base-date", (input: string) => {
                if (input) {
                  return dateConverter(input);
                }
                return DateTime.now();
              });
          },
          async (args) => {
            const scheduler = await configure(args);
            await scheduler.queueAll(args.baseDate);
          },
        )
        .command<SchedulerQueueJobArgs>(
          "create-job <collector>",
          "queue a job manually",
          (yags) => {
            yags
              .positional("collector", {
                describe: "the collector",
                type: "string",
              })
              .option("base-date", {
                type: "string",
                describe: "start-date for the manual run",
              })
              .coerce("base-date", dateConverter)
              .option("start-date", {
                type: "string",
                describe: "start-date for the manual run",
              })
              .coerce("start-date", dateConverter)
              .option("end-date", {
                type: "string",
                describe: "start-date for the manual run",
              })
              .coerce("end-date", dateConverter)
              .demandOption(["base-date", "start-date", "end-date"]);
          },
          async (args) => {
            const scheduler = await configure(args);
            await scheduler.queueJob(args.collector, args.baseDate, {
              startDate: args.startDate,
              endDate: args.endDate,
            });
          },
        );
    },
  )
  .demandCommand()
  .strict()
  .help("h")
  .alias("h", "help")
  .parse();
