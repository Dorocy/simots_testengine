'use client';

import { useMemo, useState } from 'react';
import {
  ChevronRight,
  ChevronDown,
  Box,
  Layers,
  FileText,
  Hash,
  List,
  Link2,
  Globe,
  Tag,
  CheckCircle2,
  Info,
  Cpu,
} from 'lucide-react';

// ── AAS type helpers ──────────────────────────────────────────────────────────

interface LangString {
  language: string;
  text: string;
}

interface AasShell {
  id: string;
  idShort?: string;
  displayName?: LangString[];
  description?: LangString[];
  administration?: { version?: string; revision?: string };
  assetInformation?: {
    assetKind?: string;
    globalAssetId?: string;
    assetType?: string;
  };
  submodels?: Array<{ type: string; keys: Array<{ type: string; value: string }> }>;
}

interface Submodel {
  id: string;
  idShort?: string;
  displayName?: LangString[];
  description?: LangString[];
  semanticId?: { type: string; keys: Array<{ type: string; value: string }> };
  submodelElements?: SubmodelElement[];
}

interface SubmodelElement {
  modelType?: string;
  idShort?: string;
  displayName?: LangString[];
  description?: LangString[];
  semanticId?: { type: string; keys: Array<{ type: string; value: string }> };
  value?: unknown;
  valueType?: string;
  contentType?: string;
  mimeType?: string;
  category?: string;
  // for collections / lists
  statements?: SubmodelElement[];
  // extension
  [key: string]: unknown;
}

interface AasDocument {
  assetAdministrationShells?: AasShell[];
  submodels?: Submodel[];
  conceptDescriptions?: unknown[];
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function getLang(arr?: LangString[], lang = 'en'): string {
  if (!arr?.length) return '';
  return arr.find((l) => l.language === lang)?.text ?? arr[0]?.text ?? '';
}

function getSubmodelId(ref: AasShell['submodels'][number]): string {
  return ref?.keys?.[0]?.value ?? '';
}

function getSmLabel(sm: Submodel): string {
  const display = getLang(sm.displayName);
  if (display) return display;
  if (sm.idShort) return sm.idShort;
  // derive from id — last segment after /
  const parts = sm.id?.split('/') ?? [];
  return parts[parts.length - 1] ?? sm.id ?? '(unnamed)';
}

// ── Icons per modelType ───────────────────────────────────────────────────────

const MODEL_TYPE_ICON: Record<string, React.ReactNode> = {
  Property: <Hash className="h-3 w-3 shrink-0 text-primary/70" />,
  SubmodelElementCollection: <List className="h-3 w-3 shrink-0 text-amber-500/80" />,
  SubmodelElementList: <List className="h-3 w-3 shrink-0 text-amber-500/60" />,
  File: <FileText className="h-3 w-3 shrink-0 text-sky-500/80" />,
  Blob: <FileText className="h-3 w-3 shrink-0 text-sky-500/60" />,
  MultiLanguageProperty: <Globe className="h-3 w-3 shrink-0 text-violet-400/80" />,
  ReferenceElement: <Link2 className="h-3 w-3 shrink-0 text-teal-400/80" />,
  RelationshipElement: <Link2 className="h-3 w-3 shrink-0 text-teal-400/60" />,
  AnnotatedRelationshipElement: <Link2 className="h-3 w-3 shrink-0 text-teal-400/40" />,
  Operation: <Cpu className="h-3 w-3 shrink-0 text-orange-400/80" />,
  Entity: <Box className="h-3 w-3 shrink-0 text-muted-foreground" />,
};

function getModelTypeIcon(modelType?: string): React.ReactNode {
  return modelType ? (MODEL_TYPE_ICON[modelType] ?? <Tag className="h-3 w-3 shrink-0 text-muted-foreground/50" />) : <Tag className="h-3 w-3 shrink-0 text-muted-foreground/40" />;
}

// ── Recursive element tree node ───────────────────────────────────────────────

function ElementNode({
  el,
  depth = 0,
  defaultOpen = false,
}: {
  el: SubmodelElement;
  depth?: number;
  defaultOpen?: boolean;
}) {
  const isContainer =
    el.modelType === 'SubmodelElementCollection' ||
    el.modelType === 'SubmodelElementList' ||
    el.modelType === 'Entity';

  const children: SubmodelElement[] = isContainer
    ? (Array.isArray(el.value)
        ? (el.value as SubmodelElement[])
        : Array.isArray(el.statements)
          ? (el.statements as SubmodelElement[])
          : [])
    : [];

  const [open, setOpen] = useState(defaultOpen || depth === 0);

  const displayValue = useMemo(() => {
    if (isContainer) return null;
    if (el.modelType === 'MultiLanguageProperty') {
      if (Array.isArray(el.value)) return getLang(el.value as LangString[]);
    }
    if (el.modelType === 'File' || el.modelType === 'Blob') {
      return typeof el.value === 'string' ? el.value : (el.contentType ?? el.mimeType ?? '—');
    }
    if (el.modelType === 'ReferenceElement' || el.modelType === 'RelationshipElement') {
      const ref = el.value as { keys?: Array<{ value: string }> } | undefined;
      return ref?.keys?.[0]?.value ?? JSON.stringify(el.value ?? '—');
    }
    if (el.value === null || el.value === undefined) return '—';
    if (typeof el.value === 'object') return JSON.stringify(el.value);
    return String(el.value);
  }, [el, isContainer]);

  return (
    <div style={{ paddingLeft: depth > 0 ? 16 : 0 }}>
      <div
        className={`flex items-start gap-1.5 py-1 px-2 rounded-sm group hover:bg-muted/30 transition-colors ${isContainer ? 'cursor-pointer' : ''}`}
        onClick={isContainer ? () => setOpen((o) => !o) : undefined}
      >
        {/* expand / indent */}
        <span className="mt-0.5 shrink-0 w-3 flex items-center justify-center">
          {isContainer ? (
            open
              ? <ChevronDown className="h-3 w-3 text-muted-foreground/60" />
              : <ChevronRight className="h-3 w-3 text-muted-foreground/60" />
          ) : null}
        </span>

        {/* modelType icon */}
        <span className="mt-[3px]">{getModelTypeIcon(el.modelType)}</span>

        {/* idShort */}
        <span className="text-[11px] font-mono font-semibold text-foreground/90 leading-5 min-w-0 shrink-0">
          {el.idShort ?? '(no idShort)'}
        </span>

        {/* modelType badge */}
        <span className="text-[9px] font-mono text-muted-foreground/50 leading-5 shrink-0">
          {el.modelType ?? ''}
        </span>

        {/* value */}
        {displayValue !== null && (
          <span className="text-[11px] font-mono text-muted-foreground ml-auto leading-5 truncate max-w-[280px] text-right">
            {displayValue}
          </span>
        )}

        {/* valueType badge */}
        {el.valueType && (
          <span className="text-[9px] font-mono text-primary/50 leading-5 shrink-0 ml-1">
            {el.valueType}
          </span>
        )}
      </div>

      {/* Children */}
      {isContainer && open && children.length > 0 && (
        <div className="border-l border-border/40 ml-4">
          {children.map((child, i) => (
            <ElementNode
              key={`${child.idShort ?? ''}-${i}`}
              el={child}
              depth={depth + 1}
              defaultOpen={false}
            />
          ))}
        </div>
      )}

      {/* Empty collection */}
      {isContainer && open && children.length === 0 && (
        <div style={{ paddingLeft: 16 }}>
          <div className="py-1 px-2 text-[10px] font-mono text-muted-foreground/40 italic">
            (비어 있음)
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main viewer ───────────────────────────────────────────────────────────────

export function AasViewer({ jsonContent }: { jsonContent: string }) {
  const doc = useMemo<AasDocument | null>(() => {
    try {
      return JSON.parse(jsonContent) as AasDocument;
    } catch {
      return null;
    }
  }, [jsonContent]);

  const [selectedSmId, setSelectedSmId] = useState<string | null>(null);

  const shell: AasShell | undefined = doc?.assetAdministrationShells?.[0];
  const submodels: Submodel[] = doc?.submodels ?? [];

  const selectedSm = useMemo(
    () => submodels.find((s) => s.id === selectedSmId) ?? submodels[0] ?? null,
    [selectedSmId, submodels],
  );

  if (!doc) {
    return (
      <div className="rounded-md border border-border bg-card p-6 text-center text-xs text-muted-foreground font-mono">
        JSON 파싱에 실패했습니다
      </div>
    );
  }

  return (
    <div className="rounded-b-lg border-x border-b border-[hsl(142_71%_45%_/_0.3)] bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-border bg-muted/20">
        <CheckCircle2 className="h-4 w-4 text-[hsl(142_71%_45%)]" />
        <div className="min-w-0 flex-1">
          <div className="text-xs font-semibold leading-none">
            {getLang(shell?.displayName) || shell?.idShort || 'AAS Model'}
          </div>
          <div className="text-[10px] text-muted-foreground font-mono mt-0.5 truncate">
            {shell?.id}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {shell?.assetInformation?.assetKind && (
            <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border bg-primary/8 border-primary/25 text-primary">
              {shell.assetInformation.assetKind.toUpperCase()}
            </span>
          )}
          {shell?.administration && (
            <span className="text-[9px] font-mono text-muted-foreground">
              v{shell.administration.version}.{shell.administration.revision}
            </span>
          )}
          <span className="text-[9px] font-mono text-muted-foreground border-l border-border pl-2">
            {submodels.length} submodels
          </span>
        </div>
      </div>

      {/* Shell info strip — only show globalAssetId if it differs from shell.id */}
      {shell?.assetInformation?.globalAssetId &&
        shell.assetInformation.globalAssetId !== shell?.id && (
          <div className="px-4 py-2 border-b border-border/60 bg-muted/10 flex items-center gap-2">
            <Info className="h-3 w-3 text-muted-foreground/50 shrink-0" />
            <span className="text-[10px] font-mono text-muted-foreground/60 truncate">
              {shell.assetInformation.globalAssetId}
            </span>
            {shell.description?.[0] && (
              <>
                <span className="text-muted-foreground/30 shrink-0">·</span>
                <span className="text-[10px] text-muted-foreground/60 truncate">
                  {getLang(shell.description)}
                </span>
              </>
            )}
          </div>
        )}

      {/* 2-pane: submodel list + element tree */}
      <div className="flex min-h-0 h-[520px]">
        {/* Left — submodel list */}
        <div className="w-52 shrink-0 border-r border-border overflow-y-auto">
          <div className="px-3 py-2 border-b border-border/60 bg-muted/20 sticky top-0">
            <span className="text-[9px] font-mono font-semibold text-muted-foreground uppercase tracking-widest">
              Submodels
            </span>
          </div>
          {submodels.map((sm) => {
            const active = (selectedSmId ?? submodels[0]?.id) === sm.id;
            const label = getSmLabel(sm);
            return (
              <button
                key={sm.id}
                onClick={() => setSelectedSmId(sm.id)}
                className={`w-full text-left flex items-start gap-2 px-3 py-2.5 border-b border-border/40 transition-colors last:border-b-0 ${
                  active
                    ? 'bg-primary/8 border-l-2 border-l-primary'
                    : 'hover:bg-muted/30 border-l-2 border-l-transparent'
                }`}
              >
                <Layers className={`h-3 w-3 mt-0.5 shrink-0 ${active ? 'text-primary' : 'text-muted-foreground/50'}`} />
                <div className="min-w-0">
                  <div className={`text-[11px] font-semibold leading-snug truncate ${active ? 'text-primary' : 'text-foreground/80'}`}>
                    {label}
                  </div>
                  <div className="text-[9px] font-mono text-muted-foreground/50 mt-0.5">
                    {sm.submodelElements?.length ?? 0} elements
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Right — element tree */}
        <div className="flex-1 min-w-0 overflow-y-auto">
          {selectedSm ? (
            <>
              {/* Submodel header */}
              <div className="px-4 py-2.5 border-b border-border/60 bg-muted/10 sticky top-0 flex items-center gap-2">
                <Layers className="h-3.5 w-3.5 text-primary/70 shrink-0" />
                <div className="min-w-0 flex-1">
                  <span className="text-[11px] font-semibold text-foreground/90">
                    {getSmLabel(selectedSm)}
                  </span>
                  {selectedSm.semanticId?.keys?.[0]?.value && (
                    <span className="ml-2 text-[9px] font-mono text-muted-foreground/50 truncate">
                      {selectedSm.semanticId.keys[0].value}
                    </span>
                  )}
                </div>
                <span className="text-[9px] font-mono text-muted-foreground/50 shrink-0">
                  {selectedSm.submodelElements?.length ?? 0} elements
                </span>
              </div>

              {/* Elements */}
              <div className="p-2">
                {(selectedSm.submodelElements?.length ?? 0) === 0 ? (
                  <div className="py-8 text-center text-[11px] font-mono text-muted-foreground/40">
                    서브모델 요소가 없습니다
                  </div>
                ) : (
                  selectedSm.submodelElements!.map((el, i) => (
                    <ElementNode
                      key={`${el.idShort ?? ''}-${i}`}
                      el={el}
                      depth={0}
                      defaultOpen={i < 3}
                    />
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-[11px] font-mono text-muted-foreground/40">
              서브모델을 선택하세요
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
