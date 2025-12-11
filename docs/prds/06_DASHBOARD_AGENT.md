# PRD: 블럭 F - Dashboard Agent

> **버전**: 1.0.0 | **작성일**: 2025-12-11 | **블럭 코드**: F

---

## 1. 개요

### 1.1 목적

PokerVOD 시스템의 React 기반 프론트엔드 대시보드입니다. 카탈로그 브라우징, 검색, 동기화 모니터링 기능을 제공합니다.

### 1.2 책임 범위

| 항목 | 포함 | 제외 |
|------|------|------|
| 카탈로그 브라우저 | O | |
| 검색 인터페이스 | O | |
| 동기화 모니터 | O | |
| 어드민 패널 | O | |
| 비디오 재생 | | X (외부 플레이어) |
| 데이터 수정 | | X (읽기 전용) |

---

## 2. 기술 스택

| 분류 | 기술 | 버전 |
|------|------|------|
| Framework | React | 19+ |
| Language | TypeScript | 5.0+ |
| Styling | Tailwind CSS | 3.4+ |
| State | Zustand | 4.5+ |
| Data Fetching | TanStack Query | 5.0+ |
| Routing | React Router | 6.0+ |
| UI Components | shadcn/ui | latest |
| Build | Vite | 5.0+ |

---

## 3. 페이지 구조

### 3.1 라우트 맵

```
/                           # 대시보드 홈
├── /catalog                # 카탈로그 브라우저
│   ├── /catalog/:projectCode      # 프로젝트별 뷰
│   ├── /catalog/:projectCode/:year  # 연도별 뷰
│   └── /catalog/video/:id         # 비디오 상세
├── /clips                  # 핸드 클립
│   ├── /clips/search              # 클립 검색
│   └── /clips/:id                 # 클립 상세
├── /players                # 플레이어 목록
│   └── /players/:id               # 플레이어 상세
├── /sync                   # 동기화 모니터
│   ├── /sync/nas                  # NAS 동기화
│   └── /sync/sheets               # Sheets 동기화
└── /admin                  # 어드민 패널
    ├── /admin/projects            # 프로젝트 관리
    └── /admin/tags                # 태그 관리
```

### 3.2 레이아웃

```
┌─────────────────────────────────────────────────────────────────┐
│  Header                                                          │
│  ┌──────┐  ┌─────────────────────────────────┐  ┌────────────┐ │
│  │ Logo │  │ Search Bar                       │  │ User Menu  │ │
│  └──────┘  └─────────────────────────────────┘  └────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│        │                                                         │
│  Side  │  Main Content                                          │
│  bar   │                                                         │
│        │  ┌─────────────────────────────────────────────────┐   │
│  Nav   │  │                                                  │   │
│        │  │                                                  │   │
│        │  │                                                  │   │
│        │  └─────────────────────────────────────────────────┘   │
│        │                                                         │
├─────────────────────────────────────────────────────────────────┤
│  Footer                                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 주요 컴포넌트

### 4.1 카탈로그 브라우저

```tsx
// src/pages/Catalog/CatalogBrowser.tsx
export function CatalogBrowser() {
  const { projectCode, year } = useParams();
  const [filters, setFilters] = useState<CatalogFilters>({});

  const { data: catalog, isLoading } = useQuery({
    queryKey: ['catalog', projectCode, year, filters],
    queryFn: () => catalogApi.list({ projectCode, year, ...filters }),
  });

  return (
    <div className="flex gap-4">
      <FilterSidebar filters={filters} onChange={setFilters} />
      <CatalogGrid items={catalog?.items} isLoading={isLoading} />
    </div>
  );
}
```

### 4.2 비디오 카드

```tsx
// src/components/catalog/VideoCard.tsx
interface VideoCardProps {
  video: CatalogItem;
  onClick: () => void;
}

export function VideoCard({ video, onClick }: VideoCardProps) {
  return (
    <Card onClick={onClick} className="cursor-pointer hover:shadow-lg">
      <CardHeader>
        <Thumbnail src={video.thumbnailUrl} />
        <Badge>{video.projectCode}</Badge>
      </CardHeader>
      <CardContent>
        <h3>{video.title}</h3>
        <p>{video.eventName}</p>
        <div className="flex gap-2">
          <span>{video.seasonYear}</span>
          <span>{formatDuration(video.durationSeconds)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
```

### 4.3 핸드 클립 검색

```tsx
// src/pages/Clips/ClipSearch.tsx
export function ClipSearch() {
  const [searchParams, setSearchParams] = useSearchParams();

  const tags = searchParams.getAll('tags');
  const players = searchParams.getAll('players');
  const handGrade = searchParams.get('grade');

  const { data: clips } = useQuery({
    queryKey: ['clips', tags, players, handGrade],
    queryFn: () => clipsApi.search({ tags, players, handGrade }),
  });

  return (
    <div>
      <FilterBar
        tags={tags}
        players={players}
        handGrade={handGrade}
        onChange={(filters) => setSearchParams(filters)}
      />
      <ClipGrid clips={clips?.items} />
    </div>
  );
}
```

### 4.4 동기화 모니터

```tsx
// src/pages/Sync/SyncMonitor.tsx
export function SyncMonitor() {
  const { data: status, refetch } = useQuery({
    queryKey: ['sync-status'],
    queryFn: syncApi.getStatus,
    refetchInterval: 5000,  // 5초마다 갱신
  });

  const triggerSync = useMutation({
    mutationFn: (source: string) => syncApi.trigger(source),
    onSuccess: () => refetch(),
  });

  return (
    <div className="space-y-4">
      <SyncStatusOverview status={status} />

      <div className="grid grid-cols-3 gap-4">
        {Object.entries(status?.blocks || {}).map(([blockId, blockStatus]) => (
          <BlockStatusCard key={blockId} block={blockStatus} />
        ))}
      </div>

      <div className="flex gap-2">
        <Button onClick={() => triggerSync.mutate('nas')}>
          NAS 동기화
        </Button>
        <Button onClick={() => triggerSync.mutate('sheets')}>
          Sheets 동기화
        </Button>
        <Button onClick={() => triggerSync.mutate('all')}>
          전체 동기화
        </Button>
      </div>
    </div>
  );
}
```

---

## 5. 상태 관리

### 5.1 Zustand Store

```tsx
// src/store/catalogStore.ts
interface CatalogState {
  selectedProject: string | null;
  selectedYear: number | null;
  filters: CatalogFilters;
  setProject: (code: string | null) => void;
  setYear: (year: number | null) => void;
  setFilters: (filters: CatalogFilters) => void;
  resetFilters: () => void;
}

export const useCatalogStore = create<CatalogState>((set) => ({
  selectedProject: null,
  selectedYear: null,
  filters: {},
  setProject: (code) => set({ selectedProject: code }),
  setYear: (year) => set({ selectedYear: year }),
  setFilters: (filters) => set({ filters }),
  resetFilters: () => set({ filters: {} }),
}));
```

### 5.2 React Query 설정

```tsx
// src/lib/queryClient.ts
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,  // 5분
      cacheTime: 30 * 60 * 1000, // 30분
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});
```

---

## 6. API 클라이언트

### 6.1 API 함수

```tsx
// src/api/catalog.ts
export const catalogApi = {
  list: async (params: CatalogListParams): Promise<PaginatedResponse<CatalogItem>> => {
    const response = await fetch(`${API_BASE}/catalog?${new URLSearchParams(params)}`);
    return response.json();
  },

  search: async (query: string, params: SearchParams): Promise<PaginatedResponse<CatalogItem>> => {
    const response = await fetch(`${API_BASE}/catalog/search?q=${query}&${new URLSearchParams(params)}`);
    return response.json();
  },

  stats: async (): Promise<CatalogStats> => {
    const response = await fetch(`${API_BASE}/catalog/stats`);
    return response.json();
  },
};
```

### 6.2 타입 정의

```tsx
// src/types/catalog.ts
export interface CatalogItem {
  id: string;
  title: string;
  projectCode: string;
  seasonYear: number;
  eventName: string;
  episodeType: string;
  versionType: string;
  durationSeconds: number | null;
  thumbnailUrl: string | null;
}

export interface CatalogFilters {
  project?: string;
  year?: number;
  gameType?: string;
  versionType?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  hasNext: boolean;
  hasPrev: boolean;
}
```

---

## 7. UI 컴포넌트

### 7.1 필터 사이드바

```tsx
// src/components/filters/FilterSidebar.tsx
export function FilterSidebar({ filters, onChange }: FilterSidebarProps) {
  const { data: filterOptions } = useQuery({
    queryKey: ['filter-options'],
    queryFn: catalogApi.getFilters,
  });

  return (
    <aside className="w-64 space-y-4">
      <FilterSection title="프로젝트">
        {filterOptions?.projects.map((p) => (
          <Checkbox
            key={p.code}
            label={p.name}
            checked={filters.project === p.code}
            onChange={() => onChange({ ...filters, project: p.code })}
          />
        ))}
      </FilterSection>

      <FilterSection title="연도">
        <Select
          value={filters.year}
          options={filterOptions?.years}
          onChange={(year) => onChange({ ...filters, year })}
        />
      </FilterSection>

      <FilterSection title="게임 타입">
        {filterOptions?.gameTypes.map((g) => (
          <Checkbox key={g} label={g} ... />
        ))}
      </FilterSection>
    </aside>
  );
}
```

### 7.2 태그 선택기

```tsx
// src/components/tags/TagSelector.tsx
export function TagSelector({ selectedTags, onChange }: TagSelectorProps) {
  const { data: tags } = useQuery({
    queryKey: ['tags'],
    queryFn: tagsApi.list,
  });

  const groupedTags = groupBy(tags, 'category');

  return (
    <div className="space-y-4">
      {Object.entries(groupedTags).map(([category, categoryTags]) => (
        <div key={category}>
          <h4 className="font-semibold mb-2">{category}</h4>
          <div className="flex flex-wrap gap-2">
            {categoryTags.map((tag) => (
              <TagBadge
                key={tag.id}
                tag={tag}
                selected={selectedTags.includes(tag.name)}
                onClick={() => {
                  if (selectedTags.includes(tag.name)) {
                    onChange(selectedTags.filter((t) => t !== tag.name));
                  } else {
                    onChange([...selectedTags, tag.name]);
                  }
                }}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## 8. 프로젝트 구조

```
frontend/
├── src/
│   ├── api/                    # API 클라이언트
│   │   ├── catalog.ts
│   │   ├── clips.ts
│   │   ├── sync.ts
│   │   └── index.ts
│   ├── components/             # 재사용 컴포넌트
│   │   ├── catalog/
│   │   │   ├── CatalogGrid.tsx
│   │   │   ├── VideoCard.tsx
│   │   │   └── VideoDetail.tsx
│   │   ├── clips/
│   │   │   ├── ClipCard.tsx
│   │   │   └── ClipPlayer.tsx
│   │   ├── filters/
│   │   │   ├── FilterSidebar.tsx
│   │   │   └── FilterBar.tsx
│   │   ├── tags/
│   │   │   ├── TagSelector.tsx
│   │   │   └── TagBadge.tsx
│   │   └── ui/                 # shadcn/ui 컴포넌트
│   ├── pages/                  # 페이지 컴포넌트
│   │   ├── Home.tsx
│   │   ├── Catalog/
│   │   ├── Clips/
│   │   ├── Sync/
│   │   └── Admin/
│   ├── store/                  # Zustand 스토어
│   │   ├── catalogStore.ts
│   │   └── syncStore.ts
│   ├── hooks/                  # 커스텀 훅
│   │   ├── useCatalog.ts
│   │   └── useSync.ts
│   ├── types/                  # 타입 정의
│   │   ├── catalog.ts
│   │   ├── clips.ts
│   │   └── sync.ts
│   ├── lib/                    # 유틸리티
│   │   ├── queryClient.ts
│   │   └── utils.ts
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
└── vite.config.ts
```

---

## 9. 성능 요구사항

| 지표 | 목표 |
|------|------|
| 초기 로드 | < 2초 |
| 페이지 전환 | < 500ms |
| 검색 응답 | < 500ms |
| 무한 스크롤 로드 | < 300ms |
| Lighthouse 점수 | > 90 |

### 9.1 최적화 전략

```tsx
// 1. 코드 스플리팅
const Catalog = lazy(() => import('./pages/Catalog'));
const Clips = lazy(() => import('./pages/Clips'));

// 2. 이미지 레이지 로딩
<img loading="lazy" src={thumbnailUrl} />

// 3. 가상화 (대용량 리스트)
import { useVirtualizer } from '@tanstack/react-virtual';

// 4. 메모이제이션
const MemoizedVideoCard = memo(VideoCard);
```

---

## 10. 접근성

### 10.1 WCAG 2.1 준수

```tsx
// 키보드 네비게이션
<button
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick();
    }
  }}
  aria-label="비디오 재생"
>

// 스크린 리더 지원
<div role="region" aria-label="카탈로그 목록">
  {videos.map((v) => (
    <article aria-labelledby={`video-${v.id}`}>
      <h3 id={`video-${v.id}`}>{v.title}</h3>
    </article>
  ))}
</div>

// 컬러 대비
// 최소 4.5:1 대비율 유지
```

---

## 11. 테스트

### 11.1 컴포넌트 테스트

```tsx
// src/components/catalog/__tests__/VideoCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';

describe('VideoCard', () => {
  it('renders video title', () => {
    render(<VideoCard video={mockVideo} onClick={jest.fn()} />);
    expect(screen.getByText(mockVideo.title)).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = jest.fn();
    render(<VideoCard video={mockVideo} onClick={onClick} />);
    fireEvent.click(screen.getByRole('article'));
    expect(onClick).toHaveBeenCalled();
  });
});
```

### 11.2 E2E 테스트

```tsx
// e2e/catalog.spec.ts
import { test, expect } from '@playwright/test';

test('catalog search', async ({ page }) => {
  await page.goto('/catalog');

  // 검색어 입력
  await page.fill('[data-testid="search-input"]', 'wsop 2024');
  await page.press('[data-testid="search-input"]', 'Enter');

  // 결과 확인
  await expect(page.locator('[data-testid="video-card"]')).toHaveCount(10);
});
```

---

## 12. 의존성

### 12.1 외부 의존성

| 블럭 | 제공 데이터 |
|------|-----------|
| E (API) | 모든 REST API |

### 12.2 제공 기능

- 카탈로그 브라우저 UI
- 핸드 클립 검색 UI
- 동기화 모니터 UI
- 어드민 패널 UI

---

**문서 버전**: 1.0.0
**작성일**: 2025-12-11
