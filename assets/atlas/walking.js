/* All geometry and edges come from the bundled OpenStreetMap extract. */
function makeWalkingNetwork([rawPoints, edges], venues) {
  const points = rawPoints.map(point => point.map(value => value / 1e6));
  const graph = points.map(() => []);
  const destinations = new Set(venues.map(venue => venue.walkNode));
  for (const [from, to] of edges) {
    const meters = L.latLng(points[from]).distanceTo(points[to]);
    graph[from].push([to, meters]);
    graph[to].push([from, meters]);
  }
  const trees = new Map();

  function search(source) {
    if (trees.has(source)) return trees.get(source);
    const remaining = new Set(destinations);
    const distance = new Float64Array(points.length).fill(Infinity);
    const parent = new Int32Array(points.length).fill(-1);
    const heap = [];
    function push(item) {
      let i = heap.length;
      heap.push(item);
      while (i > 0) {
        const p = (i - 1) >> 1;
        if (heap[p][1] <= item[1]) break;
        heap[i] = heap[p];
        i = p;
      }
      heap[i] = item;
    }
    function pop() {
      const first = heap[0];
      const last = heap.pop();
      if (heap.length) {
        let i = 0;
        while (i * 2 + 1 < heap.length) {
          let child = i * 2 + 1;
          if (child + 1 < heap.length && heap[child + 1][1] < heap[child][1]) child++;
          if (last[1] <= heap[child][1]) break;
          heap[i] = heap[child];
          i = child;
        }
        heap[i] = last;
      }
      return first;
    }

    distance[source] = 0;
    push([source, 0]);
    while (heap.length && remaining.size) {
      const [node, cost] = pop();
      if (cost !== distance[node]) continue;
      remaining.delete(node);
      for (const [next, meters] of graph[node]) {
        const total = cost + meters;
        if (total >= distance[next]) continue;
        distance[next] = total;
        parent[next] = node;
        push([next, total]);
      }
    }
    const result = {distance, parent};
    trees.set(source, result);
    return result;
  }

  function distance(from, to) {
    if (from.id === to.id) return 0;
    return search(from.walkNode).distance[to.walkNode] + from.walkAccessMeters + to.walkAccessMeters;
  }

  function plan(from, to) {
    const meters = distance(from, to);
    if (!Number.isFinite(meters)) return null;
    const {parent} = search(from.walkNode);
    const path = [];
    for (let node = to.walkNode; node !== -1; node = parent[node]) path.push(points[node]);
    path.reverse();
    return {meters, path, approaches: [[from.position, path[0]], [path.at(-1), to.position]]};
  }

  // Held–Karp search finds the shortest order from the first selected stop.
  function optimize(stops) {
    const [start, ...others] = stops;
    if (others.length < 2) return stops;
    const all = (1 << others.length) - 1;
    const best = Array.from({length: all + 1}, () => []);
    others.forEach((stop, i) => best[1 << i][i] = {meters: distance(start, stop), prev: -1});
    for (let mask = 1; mask <= all; mask++) {
      for (const [last, state] of best[mask].entries()) {
        if (!state) continue;
        for (let next = 0; next < others.length; next++) {
          if (mask & (1 << next)) continue;
          const step = mask | (1 << next);
          const meters = state.meters + distance(others[last], others[next]);
          if (meters < (best[step][next]?.meters ?? Infinity)) {
            best[step][next] = {meters, prev: last};
          }
        }
      }
    }
    let last = -1;
    for (const [i, state] of best[all].entries()) {
      if (state && state.meters < (best[all][last]?.meters ?? Infinity)) last = i;
    }
    if (last < 0) return stops;
    const order = [];
    for (let mask = all; last >= 0;) {
      order.push(others[last]);
      const previous = best[mask][last].prev;
      mask ^= 1 << last;
      last = previous;
    }
    return [start, ...order.reverse()];
  }
  return {distance, plan, optimize};
}
