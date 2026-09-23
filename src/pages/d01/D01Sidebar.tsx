import { ChevronDown, ChevronRight } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { AssessmentBatchId, Scene } from '../../domain'
import type { D01BatchDetailReadModel, D01TreeMaterial } from '../../selectors'

function materialTone(material: string): string {
  if (material.includes('木')) return 'wood'
  if (material.includes('金属')) return 'metal'
  if (material.includes('玻璃')) return 'glass'
  if (material.includes('混凝土')) return 'concrete'
  if (material.includes('植')) return 'planting'
  return 'other'
}

export function D01SidebarSupplement({ detail, scenes, onSelectBatch }: {
  detail: D01BatchDetailReadModel
  scenes: readonly Scene[]
  onSelectBatch: (batchId: AssessmentBatchId) => void
}) {
  const [openMaterials, setOpenMaterials] = useState(() => new Set([detail.batch.material_group]))
  const [openTypes, setOpenTypes] = useState(() => new Set([detail.batch.component_type]))
  useEffect(() => {
    setOpenMaterials((current) => new Set(current).add(detail.batch.material_group))
    setOpenTypes((current) => new Set(current).add(detail.batch.component_type))
  }, [detail.batch.component_type, detail.batch.material_group])
  function toggle(setter: (next: Set<string>) => void, current: Set<string>, key: string) {
    const next = new Set(current)
    if (next.has(key)) next.delete(key)
    else next.add(key)
    setter(next)
  }
  return <div className="d01-sidebar-supplement">
    <div className="d01-side-divider" />
    <div className="d01-side-title">当前场景</div>
    <div className="d01-scene-current">场景 {String(detail.scene_index).padStart(2, '0')} · {detail.scene.name}</div>
    <div className="d01-scene-list">
      {scenes.filter((scene) => scene.scene_id !== detail.scene.scene_id).map((scene) => (
        <div key={scene.scene_id}><span />{scene.name}</div>
      ))}
    </div>
    <div className="d01-side-divider compact" />
    <div className="d01-side-title">按材料分组</div>
    <div className="d01-tree">
      {detail.tree.map((material) => <D01MaterialTree
        key={material.material_group}
        material={material}
        activeBatchId={detail.batch.batch_id}
        materialOpen={openMaterials.has(material.material_group)}
        openTypes={openTypes}
        onToggleMaterial={() => toggle(setOpenMaterials, openMaterials, material.material_group)}
        onToggleType={(type) => toggle(setOpenTypes, openTypes, type)}
        onSelectBatch={onSelectBatch}
      />)}
    </div>
  </div>
}

function D01MaterialTree({ material, activeBatchId, materialOpen, openTypes, onToggleMaterial, onToggleType, onSelectBatch }: {
  material: D01TreeMaterial
  activeBatchId: AssessmentBatchId
  materialOpen: boolean
  openTypes: Set<string>
  onToggleMaterial: () => void
  onToggleType: (type: string) => void
  onSelectBatch: (batchId: AssessmentBatchId) => void
}) {
  const count = material.types.reduce((sum, type) => sum + type.batches.length, 0)
  const Chevron = materialOpen ? ChevronDown : ChevronRight
  return <div className="d01-tree-material-block">
    <button className="d01-tree-row level-0" type="button" aria-expanded={materialOpen} onClick={onToggleMaterial}>
      <Chevron className="d01-tree-chevron" />
      <span className={`d01-material-swatch ${materialTone(material.material_group)}`} />
      <span className="d01-tree-label">{material.material_group}</span>
      <span className="d01-tree-count">{count}组</span>
    </button>
    {materialOpen && <div className="d01-tree-branch">
      {material.types.map((type) => {
        const typeOpen = openTypes.has(type.component_type)
        const TypeChevron = typeOpen ? ChevronDown : ChevronRight
        return <div className="d01-tree-type-block" key={type.component_type}>
          <button className="d01-tree-row level-1" type="button" aria-expanded={typeOpen} onClick={() => onToggleType(type.component_type)}>
            <TypeChevron className="d01-tree-chevron" />
            <span className={`d01-mini-swatch ${materialTone(material.material_group)}`} />
            <span className="d01-tree-label">{type.component_type}</span>
            <span className="d01-tree-count">{type.batches.length}组</span>
          </button>
          {typeOpen && <div className="d01-tree-branch inner">
            {type.batches.map((batch) => <button
              className={`d01-tree-row level-2 ${batch.batch_id === activeBatchId ? 'active' : ''}`.trim()}
              type="button"
              key={batch.batch_id}
              onClick={() => onSelectBatch(batch.batch_id)}
            >
              <span className="d01-tree-label">{batch.label}</span>
              <span className="d01-tree-count">{batch.quantity}件</span>
            </button>)}
          </div>}
        </div>
      })}
    </div>}
  </div>
}
