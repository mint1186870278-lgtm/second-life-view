/**
 * Implementation-only route strings. Product Authority freezes page boundaries,
 * not these literal URL paths. W02-A and W02-B intentionally share one W02 route.
 */
export const ImplementationRoutes = {
  c01: '/create/project',
  c02: '/create/scenes',
  c03: '/create/analysis',
  w01: '/workspace/view',
  w02: '/workspace/review',
  d01: '/workspace/batches/:batchId',
} as const
