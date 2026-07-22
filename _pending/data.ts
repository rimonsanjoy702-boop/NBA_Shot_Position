import { ElMessage } from "element-plus";
import { AccountStatsLink, AccountStatsNode } from "@/models.ts";

const DATA_BASE_URL = import.meta.env.BASE_URL + 'demo-data/';

async function GET(path: string) {
  try {
    const type = path.endsWith('.json') ? 'json' : 'text';
    if (path.startsWith('/')) path = path.slice(1); // remove leading slash for fetch
    const resp = await fetch(DATA_BASE_URL + path)
    if (!resp.ok) {
      throw new Error(`Failed to fetch ${path}: ${resp.status} ${resp.statusText}`);
    }
    if (type === 'json') {
      return await resp.json();
    } else if (type === 'text') {
      return await resp.text();
    } else {
      throw new Error(`Unsupported type: ${type}`);
    }
  } catch (e) {
    console.error('Error GET ' + path)
    ElMessage.error({
      message: '发生网络错误，请重试！',
      duration: 5000000,
    });
    throw e;
  }
}

export async function loadRecommendationNodes() {
  return await GET(`/user_stat_nodes.json`) as AccountStatsNode[]
}

export async function loadRecommendationLinks() {
  return await GET(`/user_stat_links.json`) as AccountStatsLink[]
}