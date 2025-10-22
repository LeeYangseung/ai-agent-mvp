"use client"

import { Bot, Database, GitBranch } from "lucide-react"

interface SidebarProps {
  sidebarOpen: boolean
  currentPage: string
  setCurrentPage: (page: string) => void
}

export function Sidebar({ sidebarOpen, currentPage, setCurrentPage }: SidebarProps) {
  return (
    <div
      className={`${sidebarOpen ? "w-64" : "w-16"} bg-white border-r border-gray-200 transition-all duration-300 flex flex-col`}
    >
      {/* Sidebar Header */}
      <div className="p-4">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 flex items-center justify-center">
            <img src="/logo.png" alt="T Logo" className="w-8 h-8 object-contain" />
          </div>
          {sidebarOpen && (
            <div>
              <h1 className="font-semibold text-gray-800">AI Agent</h1>
            </div>
          )}
        </div>
      </div>

      {/* Sidebar Menu */}
      <div className="flex-1 p-4">
        <nav className="space-y-2">
        <button
            onClick={() => setCurrentPage("graph-editor")}
            className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
              currentPage === "graph-editor"
                ? "bg-primary/5 text-primary border border-primary/20"
                : "text-gray-700 hover:bg-gray-50"
            }`}
          >
            <GitBranch className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span className="font-medium">AI Agent 그래프 에디터</span>}
          </button>

          <button
            onClick={() => setCurrentPage("agent-management")}
            className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
              currentPage === "agent-management"
                ? "bg-primary/5 text-primary border border-primary/20"
                : "text-gray-700 hover:bg-gray-50"
            }`}
          >
            <Bot className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span className="font-medium">AI Agent 관리</span>}
          </button>

          <button
            onClick={() => setCurrentPage("knowledge-management")}
            className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
              currentPage === "knowledge-management"
                ? "bg-primary/5 text-primary border border-primary/20"
                : "text-gray-700 hover:bg-gray-50"
            }`}
          >
            <Database className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span className="font-medium">지식 관리</span>}
          </button>
        </nav>
      </div>
    </div>
  )
}
