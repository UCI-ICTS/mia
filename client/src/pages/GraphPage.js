// src/pages/ViewGraphPage.js
import { useState, useCallback, useEffect } from "react";
import { useParams, Navigate } from "react-router-dom";
import { useSelector } from "react-redux";
import { Typography } from "antd";
import {
  ReactFlowProvider,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { GraphView } from "../components/GraphComponents";

const { Paragraph, Title } = Typography;

const GraphPage = () => {
  const { script_id } = useParams();
  const isAuthenticated = useSelector((state) => state.auth.isAuthenticated);
  const scriptMeta = useSelector((state) =>
    state.data.scripts.find((s) => s.script_id === script_id)
  );
  const graphData = scriptMeta?.graph || { nodes: [], edges: [] };

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!scriptMeta) return <Navigate to="/dashboard/scripts" replace />;

  return (
    <div className="layout">
      <div className="primary-header">
        <Title className="primary-title">Consentbot Scripts</Title>
      </div>
      <Typography.Title level={4}>
        View Script: {scriptMeta.name}
      </Typography.Title>
      <Paragraph type="secondary">
        {scriptMeta.description} (Version {scriptMeta.version_number})
      </Paragraph>

      <ReactFlowProvider>
        <div style={{ width: "100%", height: "80vh", position: "relative" }}>
          <GraphView graphData={graphData} />
        </div>
      </ReactFlowProvider>
    </div>
  );
};

export default GraphPage;
