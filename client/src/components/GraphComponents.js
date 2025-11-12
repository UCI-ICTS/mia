// src/components/GraphComponents.js

import { useState, useCallback, useEffect } from "react";
import { useParams, Navigate } from "react-router-dom";
import { useSelector } from "react-redux";
import { Typography, Alert } from "antd";
import {
  Background,
  ReactFlow,
  ReactFlowProvider,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Controls,
  MiniMap,
  useReactFlow,
  Handle,
  Position
} from "@xyflow/react";
import dagre from "dagre";
import { type } from "@testing-library/user-event/dist/type";

const { Paragraph } = Typography;

/* ---------------- DAGRE LAYOUT ---------------- */
export const getLayoutedElements = (nodes, edges, direction = "TB") => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 10,
    ranksep: 30,
    marginx: 50,
    marginy: 50,
  });

  const nodeWidth = 30;
  const nodeHeight = 60;

  nodes.forEach((n) => dagreGraph.setNode(n.id, { width: nodeWidth, height: nodeHeight }));
  edges.forEach((e) => dagreGraph.setEdge(e.source, e.target));
  dagre.layout(dagreGraph);

  return nodes.map((node) => {
    const { x, y } = dagreGraph.node(node.id);
    return {
      ...node,
      position: { x: x - nodeWidth / 2, y: y - nodeHeight / 2 },
      targetPosition: direction === "LR" ? "left" : "top",
      sourcePosition: direction === "LR" ? "right" : "bottom",
    };
  });
};

/* ---------------- BOT NODE ---------------- */
export function BotNode({ data }) {
  return (
    <div
      style={{
        background: "#E0F2F1",
        border: "1px solid #26A69A",
        borderRadius: 8,
        padding: 10,
        width: 840,
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
      }}
    >
      <Handle type="target" position={Position.Top} />{console.log(data)}
      <strong>🤖 Bot: {data.id}</strong>
      <div style={{ marginTop: 6, color: "#004D40", fontSize: 13 }}>
        
        <Handle type="source" position={Position.Bottom} />
      </div>
    </div>
  );
}

/* ---------------- USER NODE ---------------- */
export function UserNode({ data }) {
  return (
    <div
      style={{
        background: "#E3F2FD",
        border: "1px solid #42A5F5",
        borderRadius: 8,
        padding: 10,
        width: 240,
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
      }}
    >
      <Handle type="target" position={Position.Top} />
      <strong>🧑 Use: {data.id}r</strong>
      <div style={{ marginTop: 6, color: "#0D47A1", fontSize: 13 }}>
        {Array.isArray(data.messages)
          ? data.messages.slice(0, 2).map((m, i) => <div key={i}>{m}</div>)
          : data.label}
        <Handle type="source" position={Position.Bottom} />
      </div>
    </div>
  );
}

/* ---------------- INNER GRAPH VIEWER ---------------- */
export const GraphView = ({ graphData }) => {
  const { fitView, setViewport, getViewport } = useReactFlow();
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);

  useEffect(() => {
    if (graphData?.nodes?.length > 0) {
      const layouted = getLayoutedElements(graphData.nodes, graphData.edges);
      setNodes(layouted);
      setEdges(graphData.edges);
      setTimeout(() => fitView({ padding: 0.2 }), 100);
    }
  }, [graphData, fitView]);

  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  const onEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );
  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    []
  );

  const processedNodes = nodes.map((n) => ({
    ...n,
    type: n.data?.type || n.type || "default",
    data: {
      ...n.data,
      id: n.id,
      label: n.data?.label || n.id,
    },
  }));

  // Handle click on MiniMap background
  const handleMiniMapClick = useCallback((event) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - bounds.left;
    const y = event.clientY - bounds.top;

    const { zoom } = getViewport();
    // Adjust panning based on current zoom
    const centerX = (x - bounds.width / 2) / zoom;
    const centerY = (y - bounds.height / 2) / zoom;

    setViewport({ x: -centerX * 4, y: -centerY * 4, zoom }, { duration: 400 });
  }, [setViewport, getViewport]);
  
const nodeTypes = {
  bot: BotNode,
  user: UserNode,
};
  
  return (
    <ReactFlow
      nodes={processedNodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      defaultViewport={{ x: 0, y: 0, zoom: 1.2 }}
    >
      <Controls />
      <MiniMap
      
        style={{ cursor: "pointer"}}
        onClick={handleMiniMapClick}
        pannable
        zoomable
      />
      <Background variant="dots" gap={12} size={1} />
    </ReactFlow>
  );
};
