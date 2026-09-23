import { creationDemoGraph } from '../fixtures'
import { FixtureProjectDataRepository } from './FixtureProjectDataRepository'
import { LocalProjectMutationService } from './LocalProjectMutationService'

export const creationProjectRepository = new FixtureProjectDataRepository(creationDemoGraph)
export const creationProjectMutationService = new LocalProjectMutationService()
