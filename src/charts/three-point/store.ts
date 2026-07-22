import { defineStore } from "pinia";
import { ref, computed } from "vue";

export interface TeamSeasonRaw {
  team_id: number;
  team_name: string;
  abbr: string;
  season_list: {
    season: string;
    total_pa: number;
    "3pa": number;
    "3par": number;
    win_pct: number | null;
    delta_3par: number | null;
    delta_3pa: number | null;
    is_turn_point: boolean;
    group_type: string;
  }[];
}

export interface GroupClassifyEntry {
  team_id: number;
  team_name: string;
  abbr: string;
  group_type: "leader" | "laggard" | "mid";
  turn_point_season: string | null;
  turn_point_reason: string | null;
  seasons_count: number;
}

export interface GroupAggEntry {
  avg_3pa: number;
  avg_3par: number;
  avg_win_pct: number;
  team_cnt: number;
}

export interface SeasonAggData {
  season: string;
  leader?: GroupAggEntry;
  mid?: GroupAggEntry;
  laggard?: GroupAggEntry;
}

export type AggDataMap = Record<string, SeasonAggData>;

/** X-axis start season — the year the leader/laggard divergence became visible */
const X_START = "2008-09";
export const useThreePointCompareStore = defineStore("threePointCompare", () => {
  // -------- state --------
  const rawData = ref<TeamSeasonRaw[]>([]);
  const classifyData = ref<GroupClassifyEntry[]>([]);
  const aggData = ref<Record<string, SeasonAggData>>({});

  const loading = ref(false);
  const error = ref<string | null>(null);

  /** Whether to show the "mid" (transition) group on the charts */
  const showMid = ref(false);

  // -------- derived --------
  const seasonList = computed<string[]>(() => {
    return Object.keys(aggData.value)
      .filter((s) => s >= X_START)
      .sort();
  });

  const leaderTeams = computed<GroupClassifyEntry[]>(() =>
    classifyData.value.filter((t) => t.group_type === "leader")
  );
  const midTeams = computed<GroupClassifyEntry[]>(() =>
    classifyData.value.filter((t) => t.group_type === "mid")
  );
  const laggardTeams = computed<GroupClassifyEntry[]>(() =>
    classifyData.value.filter((t) => t.group_type === "laggard")
  );

  // -------- actions --------
  async function loadAll() {
    loading.value = true;
    error.value = null;
    try {
      const base = "/data/three_point_compare";
      const [rawRes, classifyRes, aggRes] = await Promise.all([
        fetch(`${base}/team_season_3p_raw.json`),
        fetch(`${base}/group_classify.json`),
        fetch(`${base}/season_group_agg.json`),
      ]);

      if (!rawRes.ok || !classifyRes.ok || !aggRes.ok) {
        throw new Error("Failed to load one or more data files");
      }

      rawData.value = await rawRes.json();
      classifyData.value = await classifyRes.json();
      aggData.value = await aggRes.json();
    } catch (e: any) {
      error.value = e.message ?? "Unknown error";
    } finally {
      loading.value = false;
    }
  }

  function toggleMid(enabled: boolean) {
    showMid.value = enabled;
  }

  return {
    rawData,
    classifyData,
    aggData,
    loading,
    error,
    showMid,
    seasonList,
    leaderTeams,
    midTeams,
    laggardTeams,
    loadAll,
    toggleMid,
  };
});
