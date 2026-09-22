import {
  EVIDENCE_STATUSES,
  PATHWAYS,
  REVIEW_STATUSES,
  SCENE_INGESTION_STATUSES,
  VERIFICATION_STATUSES,
  VERIFICATION_TYPES,
  type ProjectGraph,
} from '../domain'
import { getBatchPendingVerificationCount, getBatchQuantity } from '../selectors'
import { DomainInvariantError, type InvariantIssue, type ValidationResult } from './types'

function addDuplicateIssues<T>(
  records: readonly T[],
  getId: (record: T) => string,
  collectionPath: string,
  issues: InvariantIssue[],
): void {
  const seen = new Set<string>()
  records.forEach((record, index) => {
    const id = getId(record)
    if (seen.has(id)) {
      issues.push({
        code: 'DUPLICATE_ID',
        path: `${collectionPath}[${index}]`,
        message: `Duplicate ID ${id} in ${collectionPath}.`,
      })
    }
    seen.add(id)
  })
}

function checkEnum(
  value: string,
  allowed: readonly string[],
  path: string,
  issues: InvariantIssue[],
): void {
  if (!allowed.includes(value)) {
    issues.push({ code: 'INVALID_ENUM_VALUE', path, message: `${value} is not valid for ${path}.` })
  }
}

export function validateProjectGraph(graph: ProjectGraph): ValidationResult {
  const issues: InvariantIssue[] = []

  addDuplicateIssues(graph.projects, (item) => item.project_id, 'projects', issues)
  addDuplicateIssues(graph.scenes, (item) => item.scene_id, 'scenes', issues)
  addDuplicateIssues(graph.componentInstances, (item) => item.component_instance_id, 'componentInstances', issues)
  addDuplicateIssues(graph.assessmentBatches, (item) => item.batch_id, 'assessmentBatches', issues)
  addDuplicateIssues(graph.verificationItems, (item) => item.verification_id, 'verificationItems', issues)
  addDuplicateIssues(graph.evidenceAssets, (item) => item.evidence_asset_id, 'evidenceAssets', issues)
  addDuplicateIssues(graph.humanVerifiedFacts, (item) => item.human_verified_fact_id, 'humanVerifiedFacts', issues)
  addDuplicateIssues(graph.referenceSources, (item) => item.reference_source_id, 'referenceSources', issues)
  addDuplicateIssues(graph.localOpportunities, (item) => item.local_opportunity_id, 'localOpportunities', issues)

  const projectIds = new Set(graph.projects.map((item) => item.project_id))
  const sceneById = new Map(graph.scenes.map((item) => [item.scene_id, item]))
  const batchById = new Map(graph.assessmentBatches.map((item) => [item.batch_id, item]))
  const componentIds = new Set(graph.componentInstances.map((item) => item.component_instance_id))
  const verificationIds = new Set(graph.verificationItems.map((item) => item.verification_id))

  graph.scenes.forEach((scene, index) => {
    if (!projectIds.has(scene.project_id)) {
      issues.push({ code: 'MISSING_PROJECT_REFERENCE', path: `scenes[${index}].project_id`, message: `Missing Project ${scene.project_id}.` })
    }
    checkEnum(scene.ingestion_status, SCENE_INGESTION_STATUSES, `scenes[${index}].ingestion_status`, issues)
  })

  graph.assessmentBatches.forEach((batch, index) => {
    if (!projectIds.has(batch.project_id)) {
      issues.push({ code: 'MISSING_PROJECT_REFERENCE', path: `assessmentBatches[${index}].project_id`, message: `Missing Project ${batch.project_id}.` })
    }
    const scene = sceneById.get(batch.scene_id)
    if (!scene) {
      issues.push({ code: 'MISSING_SCENE_REFERENCE', path: `assessmentBatches[${index}].scene_id`, message: `Missing Scene ${batch.scene_id}.` })
    } else if (scene.project_id !== batch.project_id) {
      issues.push({ code: 'PROJECT_REFERENCE_MISMATCH', path: `assessmentBatches[${index}].scene_id`, message: `Batch and Scene belong to different Projects.` })
    }
    checkEnum(batch.pathway, PATHWAYS, `assessmentBatches[${index}].pathway`, issues)
    checkEnum(batch.evidence_status, EVIDENCE_STATUSES, `assessmentBatches[${index}].evidence_status`, issues)
    checkEnum(batch.review_status, REVIEW_STATUSES, `assessmentBatches[${index}].review_status`, issues)

    if (batch.denormalized_quantity !== undefined) {
      const canonical = getBatchQuantity(batch.batch_id, graph.componentInstances)
      if (batch.denormalized_quantity !== canonical) {
        issues.push({ code: 'BATCH_QUANTITY_DRIFT', path: `assessmentBatches[${index}].denormalized_quantity`, message: `Cached quantity ${batch.denormalized_quantity} differs from canonical ${canonical}.` })
      }
    }
    if (batch.denormalized_pending_verification_count !== undefined) {
      const canonical = getBatchPendingVerificationCount(batch.batch_id, graph.verificationItems)
      if (batch.denormalized_pending_verification_count !== canonical) {
        issues.push({ code: 'BATCH_PENDING_COUNT_DRIFT', path: `assessmentBatches[${index}].denormalized_pending_verification_count`, message: `Cached pending count ${batch.denormalized_pending_verification_count} differs from canonical ${canonical}.` })
      }
    }
  })

  graph.componentInstances.forEach((instance, index) => {
    if (!projectIds.has(instance.project_id)) {
      issues.push({ code: 'MISSING_PROJECT_REFERENCE', path: `componentInstances[${index}].project_id`, message: `Missing Project ${instance.project_id}.` })
    }
    const scene = sceneById.get(instance.scene_id)
    if (!scene) {
      issues.push({ code: 'MISSING_SCENE_REFERENCE', path: `componentInstances[${index}].scene_id`, message: `Missing Scene ${instance.scene_id}.` })
    } else if (scene.project_id !== instance.project_id) {
      issues.push({ code: 'PROJECT_REFERENCE_MISMATCH', path: `componentInstances[${index}].scene_id`, message: `Component and Scene belong to different Projects.` })
    }
    if (instance.batch_id) {
      const batch = batchById.get(instance.batch_id)
      if (!batch) {
        issues.push({ code: 'MISSING_BATCH_REFERENCE', path: `componentInstances[${index}].batch_id`, message: `Missing Batch ${instance.batch_id}.` })
      } else {
        if (batch.project_id !== instance.project_id) {
          issues.push({ code: 'PROJECT_REFERENCE_MISMATCH', path: `componentInstances[${index}].batch_id`, message: `Component and Batch belong to different Projects.` })
        }
        if (batch.scene_id !== instance.scene_id) {
          issues.push({ code: 'BATCH_SCENE_MISMATCH', path: `componentInstances[${index}].scene_id`, message: `Component Scene ${instance.scene_id} differs from Batch Scene ${batch.scene_id}.` })
        }
      }
    }
  })

  graph.verificationItems.forEach((item, index) => {
    if (!batchById.has(item.batch_id)) {
      issues.push({ code: 'MISSING_BATCH_REFERENCE', path: `verificationItems[${index}].batch_id`, message: `Missing Batch ${item.batch_id}.` })
    }
    checkEnum(item.verification_type, VERIFICATION_TYPES, `verificationItems[${index}].verification_type`, issues)
    checkEnum(item.status, VERIFICATION_STATUSES, `verificationItems[${index}].status`, issues)
  })

  graph.evidenceAssets.forEach((asset, index) => {
    if (!projectIds.has(asset.project_id)) issues.push({ code: 'MISSING_PROJECT_REFERENCE', path: `evidenceAssets[${index}].project_id`, message: `Missing Project ${asset.project_id}.` })
    if (!batchById.has(asset.batch_id)) issues.push({ code: 'MISSING_BATCH_REFERENCE', path: `evidenceAssets[${index}].batch_id`, message: `Missing Batch ${asset.batch_id}.` })
    if (asset.scene_id && !sceneById.has(asset.scene_id)) issues.push({ code: 'MISSING_SCENE_REFERENCE', path: `evidenceAssets[${index}].scene_id`, message: `Missing Scene ${asset.scene_id}.` })
    if (asset.component_instance_id && !componentIds.has(asset.component_instance_id)) issues.push({ code: 'MISSING_COMPONENT_REFERENCE', path: `evidenceAssets[${index}].component_instance_id`, message: `Missing Component ${asset.component_instance_id}.` })
  })

  graph.humanVerifiedFacts.forEach((fact, index) => {
    if (!projectIds.has(fact.project_id)) issues.push({ code: 'MISSING_PROJECT_REFERENCE', path: `humanVerifiedFacts[${index}].project_id`, message: `Missing Project ${fact.project_id}.` })
    if (!batchById.has(fact.batch_id)) issues.push({ code: 'MISSING_BATCH_REFERENCE', path: `humanVerifiedFacts[${index}].batch_id`, message: `Missing Batch ${fact.batch_id}.` })
    if (!componentIds.has(fact.component_instance_id)) issues.push({ code: 'MISSING_COMPONENT_REFERENCE', path: `humanVerifiedFacts[${index}].component_instance_id`, message: `Missing Component ${fact.component_instance_id}.` })
    if (fact.verification_id && !verificationIds.has(fact.verification_id)) issues.push({ code: 'MISSING_VERIFICATION_REFERENCE', path: `humanVerifiedFacts[${index}].verification_id`, message: `Missing VerificationItem ${fact.verification_id}.` })
  })

  for (const [collection, records] of [
    ['referenceSources', graph.referenceSources],
    ['localOpportunities', graph.localOpportunities],
  ] as const) {
    records.forEach((record, index) => {
      if (!projectIds.has(record.project_id)) issues.push({ code: 'MISSING_PROJECT_REFERENCE', path: `${collection}[${index}].project_id`, message: `Missing Project ${record.project_id}.` })
      record.batch_ids?.forEach((batchId) => {
        if (!batchById.has(batchId)) issues.push({ code: 'MISSING_BATCH_REFERENCE', path: `${collection}[${index}].batch_ids`, message: `Missing Batch ${batchId}.` })
      })
    })
  }

  return { valid: issues.length === 0, issues }
}

export function assertValidProjectGraph(graph: ProjectGraph): void {
  const result = validateProjectGraph(graph)
  if (!result.valid) throw new DomainInvariantError(result.issues)
}
