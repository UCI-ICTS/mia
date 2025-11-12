// src/pages/ViewGraphPage.js

import React from "react";
import { useParams, Navigate } from "react-router-dom";
import { useSelector } from "react-redux";
import { Typography, Alert } from "antd";

const { Paragraph } = Typography;

const ScriptNode = ({ nodeId, scriptMap, visited }) => {
  if (!nodeId || visited.has(nodeId)) return null;
  visited.add(nodeId);

  const node = scriptMap[nodeId];
  if (!node) return null;

  return (
    <div key={nodeId} style={{ marginBottom: 20 }}>
      <div
        style={{
          backgroundColor: node.type === "bot" ? "#e0f2f1" : "#e3f2fd",
          padding: 12,
          borderRadius: 6,
        }}
      >
        <strong>{node.type === "bot" ? "Bot" : "User"}:</strong>
        {node.messages?.map((msg, i) => (
          <div key={i} dangerouslySetInnerHTML={{ __html: msg }} />
        ))}
        {node.html_content && (
          <div
            dangerouslySetInnerHTML={{ __html: node.html_content }}
            style={{ marginTop: 6 }}
          />
        )}
      </div>

      {/* Render all children recursively */}
      <div>
        {node.child_ids?.map((childId) => (
          <ScriptNode
            key={childId}
            nodeId={childId}
            scriptMap={scriptMap}
            visited={visited}
          />
        ))}
      </div>
    </div>
  );
};

const ViewGraphPage = () => {
  const { script_id } = useParams();
  const isAuthenticated = useSelector((state) => state.auth.isAuthenticated);
  const scriptMeta = useSelector((state) =>
    state.data.scripts.find((s) => s.script_id === script_id)
  );
  const scriptMap = scriptMeta?.script || {};

  // 🔒 Redirect unauthenticated users
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // ❌ Redirect if script isn't in Redux state (likely due to direct navigation)
  if (!scriptMeta) {
    console.log("OOPS")
    return <Navigate to="/dashboard/scripts" replace />;
  }

  const rootNodeId = Object.keys(scriptMap).find((key) =>
    scriptMap[key]?.parent_ids?.includes("start")
  );

  return (
    <div style={{ padding: 24 }}>
      <div className="primary-header">
        <Title className="primary-title">Consentbot Scripts</Title>
      </div>
      <Typography.Title level={4}>
        View Script: {scriptMeta.name}
      </Typography.Title>
      <Paragraph type="secondary">
        {scriptMeta.description} (Version {scriptMeta.version_number})
      </Paragraph>

      {rootNodeId ? (
        <ScriptNode
          nodeId={rootNodeId}
          scriptMap={scriptMap}
          visited={new Set()}
        />
      ) : (
        <Alert type="warning" message="Root of the script not found." />
      )}
    </div>
  );
};

export default ViewGraphPage;
