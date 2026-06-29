#include <bits/stdc++.h>
using namespace std;

struct Point {
    long long x, y;
};

struct PolarNode {
    long long x, y;
    int id;
};

constexpr int INF = 1'000'000'000;

long long gcdAbs(long long a, long long b) {
    return std::gcd(llabs(a), llabs(b));
}

int half(const PolarNode &p) {
    return (p.y > 0 || (p.y == 0 && p.x >= 0)) ? 0 : 1;
}

long long cross(const PolarNode &a, const PolarNode &b) {
    return a.x * b.y - a.y * b.x;
}

bool polarLess(const PolarNode &a, const PolarNode &b) {
    int ha = half(a), hb = half(b);
    if (ha != hb) return ha < hb;
    long long cr = cross(a, b);
    if (cr != 0) return cr > 0;
    return a.id < b.id;
}

struct SegTree {
    int n = 1;
    vector<int> tree;

    void build(const vector<int> &a) {
        n = 1;
        while (n < (int)a.size()) n <<= 1;
        tree.assign(n << 1, INF);
        for (int i = 0; i < (int)a.size(); ++i) tree[n + i] = a[i];
        for (int i = n - 1; i > 0; --i) tree[i] = min(tree[i << 1], tree[i << 1 | 1]);
    }

    int query(int l, int r) const {
        int ans = INF;
        for (l += n, r += n; l < r; l >>= 1, r >>= 1) {
            if (l & 1) ans = min(ans, tree[l++]);
            if (r & 1) ans = min(ans, tree[--r]);
        }
        return ans;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;

    vector<Point> p(n + 1);
    vector<PolarNode> nodes;
    nodes.reserve(n);
    map<pair<long long, long long>, int> lineIndex;
    vector<pair<long long, long long>> lines;
    vector<array<bool, 2>> raySeen;

    for (int i = 1; i <= n; ++i) {
        cin >> p[i].x >> p[i].y;
        if (p[i].x != 0 || p[i].y != 0) {
            nodes.push_back({p[i].x, p[i].y, i});
            long long g = gcdAbs(p[i].x, p[i].y);
            long long dx = p[i].x / g, dy = p[i].y / g;
            if (dx < 0 || (dx == 0 && dy < 0)) {
                dx = -dx;
                dy = -dy;
            }
            auto key = make_pair(dx, dy);
            if (!lineIndex.count(key)) {
                int idx = (int)lines.size();
                lineIndex[key] = idx;
                lines.push_back(key);
                raySeen.push_back({false, false});
            }
            int idx = lineIndex[key];
            long long dot = p[i].x * dx + p[i].y * dy;
            raySeen[idx][dot > 0 ? 0 : 1] = true;
        }
    }

    vector<vector<int>> graph(n + 1);
    for (int i = 0; i < m; ++i) {
        int u, v;
        cin >> u >> v;
        graph[u].push_back(v);
    }

    vector<vector<int>> dist(n + 1, vector<int>(n + 1, INF));
    queue<int> q;
    for (int s = 1; s <= n; ++s) {
        dist[s][s] = 0;
        q.push(s);
        while (!q.empty()) {
            int u = q.front();
            q.pop();
            for (int v : graph[u]) {
                if (dist[s][v] == INF) {
                    dist[s][v] = dist[s][u] + 1;
                    q.push(v);
                }
            }
        }
    }

    sort(nodes.begin(), nodes.end(), polarLess);
    int cnt = (int)nodes.size();
    vector<int> bestEnd(n + 1, INF), answer(n + 1, INF);

    if (cnt >= 3) {
        vector<PolarNode> doubled = nodes;
        doubled.insert(doubled.end(), nodes.begin(), nodes.end());

        auto lowerAngle = [&](long long x, long long y) {
            PolarNode key{x, y, numeric_limits<int>::min()};
            return (int)(lower_bound(nodes.begin(), nodes.end(), key, polarLess) - nodes.begin());
        };

        auto upperAngle = [&](long long x, long long y) {
            PolarNode key{x, y, numeric_limits<int>::max()};
            return (int)(upper_bound(nodes.begin(), nodes.end(), key, polarLess) - nodes.begin());
        };

        auto angleLessNoTie = [&](long long ax, long long ay, long long bx, long long by) {
            PolarNode a{ax, ay, 0}, b{bx, by, 0};
            return polarLess(a, b);
        };

        SegTree seg;
        vector<int> values(cnt * 2);

        for (const auto &mid : nodes) {
            int b = mid.id;

            for (int i = 0; i < cnt; ++i) {
                int a = nodes[i].id;
                int val = INF;
                if (dist[1][a] < INF && dist[a][b] < INF) {
                    val = dist[1][a] + dist[a][b];
                }
                values[i] = values[i + cnt] = val;
            }
            seg.build(values);

            for (const auto &last : nodes) {
                int c = last.id;
                long long cr = cross(mid, last);
                if (cr == 0 || dist[b][c] == INF) continue;

                long long sx, sy, ex, ey;
                if (cr > 0) {
                    sx = -mid.x, sy = -mid.y;
                    ex = -last.x, ey = -last.y;
                } else {
                    sx = -last.x, sy = -last.y;
                    ex = -mid.x, ey = -mid.y;
                }

                int l = upperAngle(sx, sy);
                int r = lowerAngle(ex, ey);
                if (!angleLessNoTie(sx, sy, ex, ey)) r += cnt;

                int prefix = seg.query(l, r);
                if (prefix < INF) {
                    bestEnd[c] = min(bestEnd[c], prefix + dist[b][c]);
                }
            }
        }

        for (const auto &last : nodes) {
            int c = last.id;
            if (bestEnd[c] == INF) continue;
            for (int k = 1; k <= n; ++k) {
                if (dist[c][k] < INF) {
                    answer[k] = min(answer[k], bestEnd[c] + dist[c][k]);
                }
            }
        }
    }

    vector<array<int, 16>> stateDist(n + 1);
    queue<pair<int, int>> bfs;
    for (int lineId = 0; lineId < (int)lines.size(); ++lineId) {
        if (!raySeen[lineId][0] || !raySeen[lineId][1]) continue;

        long long dx = lines[lineId].first;
        long long dy = lines[lineId].second;
        vector<int> category(n + 1, 0);
        for (int i = 1; i <= n; ++i) {
            if (p[i].x == 0 && p[i].y == 0) continue;
            long long cr = dx * p[i].y - dy * p[i].x;
            if (cr == 0) {
                long long dot = p[i].x * dx + p[i].y * dy;
                category[i] = dot > 0 ? 1 : 2;
            } else {
                category[i] = cr > 0 ? 4 : 8;
            }
        }

        for (int i = 1; i <= n; ++i) stateDist[i].fill(INF);
        int startMask = category[1];
        stateDist[1][startMask] = 0;
        bfs.push({1, startMask});

        while (!bfs.empty()) {
            auto [u, mask] = bfs.front();
            bfs.pop();
            int cur = stateDist[u][mask];
            for (int v : graph[u]) {
                int nextMask = mask | category[v];
                if (stateDist[v][nextMask] == INF) {
                    stateDist[v][nextMask] = cur + 1;
                    bfs.push({v, nextMask});
                }
            }
        }

        for (int v = 1; v <= n; ++v) {
            int cur = stateDist[v][15];
            if (cur == INF) continue;
            for (int k = 1; k <= n; ++k) {
                if (dist[v][k] < INF) {
                    answer[k] = min(answer[k], cur + dist[v][k]);
                }
            }
        }
    }

    for (int i = 1; i <= n; ++i) {
        cout << (answer[i] == INF ? -1 : answer[i]) << '\n';
    }

    return 0;
}
