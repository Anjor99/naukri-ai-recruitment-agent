let graphData = null;
let currentGraphElements = null;
let graphResizeObserver = null;


async function loadGraph() {

    const container =
        document.getElementById(
            "graph-container"
        );

    container.innerHTML = `
        <div class="graph-loading">
            Loading agent graph...
        </div>
    `;

    try {

        const result =
            await API.graph();

        graphData =
            result.data;

        renderGraph(
            graphData
        );

    } catch (error) {

        container.innerHTML = `
            <div class="graph-error">
                Failed to load agent graph.
                <br>
                ${escapeHtml(
                    error.message
                )}
            </div>
        `;
    }
}


function renderGraph(data) {

    const container =
        document.getElementById(
            "graph-container"
        );

    if (
        !data ||
        !data.nodes ||
        !data.edges
    ) {

        container.innerHTML = `
            <div class="graph-error">
                Invalid graph data.
            </div>
        `;

        return;
    }

    /*
     * Nodes and edges come entirely from /graph.
     * Nothing here knows what nodes your LangGraph contains.
     *
     * The graph is a DAG, not a straight line: router can
     * fan out to several nodes, and several nodes can merge
     * back into the same one (e.g. rag/field_selector/unknown
     * all feeding into response). So instead of flattening
     * everything into one topological column, we group nodes
     * into "levels" (their longest distance from the start)
     * and lay each level out as a row, then draw the real
     * edges on top with an SVG overlay.
     */

    const nodes =
        data.nodes.filter(
            node =>
                ![
                    "__start__",
                    "__end__"
                ].includes(node.id)
        );

    const edges =
        data.edges.filter(
            edge =>
                ![
                    "__start__",
                    "__end__"
                ].includes(edge.source) &&
                ![
                    "__start__",
                    "__end__"
                ].includes(edge.target)
        );


    const levels =
        groupNodesByLevel(
            nodes,
            edges
        );


    container.innerHTML = "";


    const graph =
        document.createElement(
            "div"
        );

    graph.className =
        "agent-graph";


    const svg =
        document.createElementNS(
            "http://www.w3.org/2000/svg",
            "svg"
        );

    svg.setAttribute(
        "class",
        "graph-edges-svg"
    );

    svg.innerHTML = `
        <defs>
            <marker
                id="graph-arrow"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
            >
                <path
                    d="M0,0 L10,5 L0,10 z"
                    fill="var(--text-muted)"
                ></path>
            </marker>
        </defs>
    `;

    graph.appendChild(svg);


    levels.forEach(
        levelNodes => {

            const row =
                document.createElement(
                    "div"
                );

            row.className =
                "graph-level";

            levelNodes.forEach(
                node => {

                    row.appendChild(
                        createGraphNode(
                            node
                        )
                    );
                }
            );

            graph.appendChild(
                row
            );
        }
    );


    container.appendChild(
        graph
    );


    drawGraphEdges(
        graph,
        svg,
        edges
    );

    currentGraphElements = {
        graph,
        svg,
        edges
    };

    if (graphResizeObserver) {

        graphResizeObserver.disconnect();
    }

    if (window.ResizeObserver) {

        graphResizeObserver =
            new ResizeObserver(
                () => refreshGraphLayout()
            );

        graphResizeObserver.observe(
            graph
        );
    }
}


/*
 * Redraws the current graph's edges using its already-rendered
 * nodes. Needed because the graph panel can be measured while
 * hidden behind the Chat tab (display: none reports zero size),
 * so its edges must be recomputed once the panel is actually
 * shown and has real dimensions.
 */
function refreshGraphLayout() {

    if (!currentGraphElements) {
        return;
    }

    drawGraphEdges(
        currentGraphElements.graph,
        currentGraphElements.svg,
        currentGraphElements.edges
    );
}


/*
 * Groups nodes into rows based on the longest path from any
 * root node (a node with no incoming edges). This keeps
 * branches (router -> rag / status / unknown) side by side
 * instead of stacked in an arbitrary single-file order, and
 * makes nodes that merge back together (e.g. -> response)
 * line up after everything that feeds into them.
 */
function groupNodesByLevel(
    nodes,
    edges
) {

    const nodeIds =
        nodes.map(
            node => node.id
        );

    const adjacency =
        new Map(
            nodeIds.map(
                id => [id, []]
            )
        );

    const indegree =
        new Map(
            nodeIds.map(
                id => [id, 0]
            )
        );

    edges.forEach(
        edge => {

            if (
                adjacency.has(edge.source) &&
                indegree.has(edge.target)
            ) {

                adjacency
                    .get(edge.source)
                    .push(edge.target);

                indegree.set(
                    edge.target,
                    indegree.get(edge.target) + 1
                );
            }
        }
    );


    const level =
        new Map(
            nodeIds.map(
                id => [id, 0]
            )
        );

    const remainingIndegree =
        new Map(indegree);

    const queue =
        nodeIds.filter(
            id => indegree.get(id) === 0
        );


    while (queue.length) {

        const id =
            queue.shift();

        adjacency
            .get(id)
            .forEach(
                target => {

                    level.set(
                        target,
                        Math.max(
                            level.get(target),
                            level.get(id) + 1
                        )
                    );

                    const next =
                        remainingIndegree.get(target) - 1;

                    remainingIndegree.set(
                        target,
                        next
                    );

                    if (next === 0) {

                        queue.push(
                            target
                        );
                    }
                }
            );
    }


    const nodeMap =
        new Map(
            nodes.map(
                node => [node.id, node]
            )
        );

    const groups =
        new Map();

    nodeIds.forEach(
        id => {

            const lvl =
                level.get(id) || 0;

            if (!groups.has(lvl)) {
                groups.set(lvl, []);
            }

            groups
                .get(lvl)
                .push(
                    nodeMap.get(id)
                );
        }
    );


    return [...groups.entries()]
        .sort(
            (a, b) => a[0] - b[0]
        )
        .map(
            ([, groupNodes]) => groupNodes
        );
}


/*
 * Draws every real edge from /graph as a curve between the
 * actual rendered positions of its source and target nodes,
 * so branching and merging show up instead of being flattened
 * into a straight top-to-bottom line. Conditional edges (the
 * router's branches) are dashed and accent-colored.
 */
function drawGraphEdges(
    graph,
    svg,
    edges
) {

    const graphRect =
        graph.getBoundingClientRect();

    const width =
        graph.scrollWidth;

    const height =
        graph.scrollHeight;

    svg.setAttribute(
        "width",
        width
    );

    svg.setAttribute(
        "height",
        height
    );

    svg.setAttribute(
        "viewBox",
        `0 0 ${width} ${height}`
    );

    svg
        .querySelectorAll(
            "path.graph-edge"
        )
        .forEach(
            path => path.remove()
        );


    edges.forEach(
        edge => {

            const sourceEl =
                findGraphNodeElement(
                    graph,
                    edge.source
                );

            const targetEl =
                findGraphNodeElement(
                    graph,
                    edge.target
                );

            if (
                !sourceEl ||
                !targetEl
            ) {
                return;
            }

            const sourceRect =
                sourceEl.getBoundingClientRect();

            const targetRect =
                targetEl.getBoundingClientRect();

            const x1 =
                sourceRect.left +
                sourceRect.width / 2 -
                graphRect.left;

            const y1 =
                sourceRect.bottom -
                graphRect.top;

            const x2 =
                targetRect.left +
                targetRect.width / 2 -
                graphRect.left;

            const y2 =
                targetRect.top -
                graphRect.top;

            const midY =
                (y1 + y2) / 2;

            const path =
                document.createElementNS(
                    "http://www.w3.org/2000/svg",
                    "path"
                );

            path.setAttribute(
                "d",
                `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`
            );

            path.setAttribute(
                "class",
                "graph-edge" +
                (edge.conditional
                    ? " graph-edge-conditional"
                    : "")
            );

            path.setAttribute(
                "marker-end",
                "url(#graph-arrow)"
            );

            svg.appendChild(
                path
            );
        }
    );
}


function findGraphNodeElement(
    graph,
    nodeId
) {

    if (
        window.CSS &&
        CSS.escape
    ) {

        return graph.querySelector(
            `[data-node-id="${CSS.escape(nodeId)}"]`
        );
    }

    return [...graph.querySelectorAll("[data-node-id]")]
        .find(
            element =>
                element.dataset.nodeId === nodeId
        ) || null;
}


function createGraphNode(node) {

    const element =
        document.createElement(
            "div"
        );

    let nodeClass =
        "graph-node";

    const id =
        node.id.toLowerCase();

    if (
        id.includes("router")
    ) {
        nodeClass +=
            " graph-node-router";
    }

    else if (
        id.includes("response")
    ) {
        nodeClass +=
            " graph-node-response";
    }

    else {
        nodeClass +=
            " graph-node-processing";
    }

    element.className =
        nodeClass;

    element.dataset.nodeId =
        node.id;

    element.innerHTML = `

        <div class="graph-node-indicator"></div>

        <div class="graph-node-content">

            <strong>
                ${escapeHtml(
                    node.label
                )}
            </strong>

            <span>
                ${escapeHtml(
                    node.id
                )}
            </span>

        </div>
    `;

    return element;
}


function highlightGraphNode(
    nodeId
) {

    document
        .querySelectorAll(
            ".graph-node"
        )
        .forEach(
            node => {

                node.classList.toggle(
                    "active",
                    node.dataset.nodeId ===
                    nodeId
                );
            }
        );
}