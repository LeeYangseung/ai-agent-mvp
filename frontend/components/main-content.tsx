"use client"
import { AgentManagementPage } from "@/components/agent-management-page"
import { KnowledgeManagementPage } from "@/components/knowledge-management-page"
import { GraphEditor } from "@/components/graph-editor"

interface MainContentProps {
  currentPage: string
}

export function MainContent({ currentPage }: MainContentProps) {
  switch (currentPage) {
    case "agent-management":
      return <AgentManagementPage />
    case "knowledge-management":
      return <KnowledgeManagementPage />
    case "graph-editor":
      return <GraphEditor />
    default:
      return <GraphEditor />
  }
}
