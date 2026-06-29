#include "testlib.h"
#include <bits/stdc++.h>
using namespace std;

struct SegTree {
    int n;
    vector<int> mn, mx;

    explicit SegTree(const vector<int>& a) {
        int sz = (int)a.size() - 1;
        n = 1;
        while (n < sz) n <<= 1;
        mn.assign(n << 1, INT_MAX);
        mx.assign(n << 1, INT_MIN);
        for (int i = 1; i <= sz; ++i) {
            mn[n + i - 1] = a[i];
            mx[n + i - 1] = a[i];
        }
        for (int i = n - 1; i >= 1; --i) {
            mn[i] = min(mn[i << 1], mn[i << 1 | 1]);
            mx[i] = max(mx[i << 1], mx[i << 1 | 1]);
        }
    }

    int queryMin(int l, int r) const {
        int res = INT_MAX;
        l += n - 1;
        r += n - 1;
        while (l <= r) {
            if (l & 1) res = min(res, mn[l++]);
            if (!(r & 1)) res = min(res, mn[r--]);
            l >>= 1;
            r >>= 1;
        }
        return res;
    }

    int queryMax(int l, int r) const {
        int res = INT_MIN;
        l += n - 1;
        r += n - 1;
        while (l <= r) {
            if (l & 1) res = max(res, mx[l++]);
            if (!(r & 1)) res = max(res, mx[r--]);
            l >>= 1;
            r >>= 1;
        }
        return res;
    }
};

int main(int argc, char* argv[]) {
    registerTestlibCmd(argc, argv);

    int n = inf.readInt();
    int m = inf.readInt();

    vector<array<int, 4>> constraints(m);
    for (int id = 0; id < m; ++id) {
        int op = inf.readInt();
        int i = inf.readInt();
        int j = inf.readInt();
        int k = inf.readInt();
        constraints[id] = {op, i, j, k};
    }

    int juryFirst = ans.readInt(-1, n, "jury first token");

    int first = ouf.readInt(-1, n, "first token");
    if (juryFirst == -1) {
        if (first != -1) {
            quitf(_wa, "participant printed a permutation, but no solution exists");
        }
        ouf.readEof();
        quitf(_ok, "correctly reported no solution");
    }

    if (first == -1) {
        quitf(_wa, "participant reported no solution, but a solution exists");
    }

    vector<int> p(n + 1);
    vector<int> seen(n + 1, 0);
    p[1] = first;

    auto acceptValue = [&](int pos, int value) {
        if (value < 1 || value > n) {
            quitf(_wa, "p[%d] = %d is outside [1, %d]", pos, value, n);
        }
        if (seen[value]) {
            quitf(_wa, "value %d appears more than once", value);
        }
        seen[value] = 1;
        p[pos] = value;
    };

    acceptValue(1, first);
    for (int i = 2; i <= n; ++i) {
        int value = ouf.readInt(1, n, format("p[%d]", i).c_str());
        acceptValue(i, value);
    }
    ouf.readEof();

    SegTree st(p);
    for (int id = 0; id < m; ++id) {
        auto [op, i, j, k] = constraints[id];
        if (op == 0) {
            int got = st.queryMin(i, k);
            if (p[j] != got) {
                quitf(_wa,
                      "constraint %d failed: expected p[%d] to be min on [%d,%d], p[%d]=%d, min=%d",
                      id + 1, j, i, k, j, p[j], got);
            }
        } else {
            int got = st.queryMax(i, k);
            if (p[j] != got) {
                quitf(_wa,
                      "constraint %d failed: expected p[%d] to be max on [%d,%d], p[%d]=%d, max=%d",
                      id + 1, j, i, k, j, p[j], got);
            }
        }
    }

    quitf(_ok, "valid permutation");
}
