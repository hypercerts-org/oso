import { gql } from "../__generated__/gql";

const GET_ALL_ARTIFACTS = gql(`
  query Artifacts {
    artifact {
      id
      name
      namespace
      url
      type
    }
  }
`);

const GET_ALL_PROJECTS = gql(`
  query Projects {
    project {
      id
      name
      slug
    }
  }
`);

const GET_ARTIFACT_BY_NAME = gql(`
  query ArtifactByName($namespace: artifact_namespace_enum!, $name: String!) {
    artifact(where: { name: { _eq: $name }, namespace: { _eq: $namespace } }) {
      id
      name
      namespace
      type
      url
    }
  }
`);

const GET_PROJECT_BY_SLUG = gql(`
  query ProjectBySlug($slug: String!) {
    project(where: { slug: { _eq: $slug } }) {
      id
      name
      slug
      verified
      description
    }
  }
`);

const GET_EVENTS_DAILY_BY_ARTIFACT = gql(`
  query EventsDailyByArtifact(
    $ids: [Int!],
    $types: [event_type_enum!],
    $startDate: timestamptz!,
    $endDate: timestamptz!, 
  ) {
    events_daily_by_artifact(where: {
      toId: {_in: $ids},
      type: {_in: $types},
      bucketDaily: {_gte: $startDate, _lte: $endDate}
    }) {
      type
      toId
      bucketDaily
      amount
    }
  }
`);

const GET_EVENTS_DAILY_BY_PROJECT = gql(`
  query EventsDailyByProject(
    $ids: [Int!],
    $types: [event_type_enum!],
    $startDate: timestamptz!,
    $endDate: timestamptz!, 
  ) {
    events_daily_by_project(where: {
      projectId: {_in: $ids}
      type: {_in: $types},
      bucketDaily: {_gte: $startDate, _lte: $endDate}
    }) {
      type
      projectId
      bucketDaily
      amount
    }
  }
`);

export {
  GET_ALL_ARTIFACTS,
  GET_ARTIFACT_BY_NAME,
  GET_ALL_PROJECTS,
  GET_PROJECT_BY_SLUG,
  GET_EVENTS_DAILY_BY_ARTIFACT,
  GET_EVENTS_DAILY_BY_PROJECT,
};
