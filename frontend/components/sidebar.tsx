"use client"

import { Bot, Database, GitBranch, ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"

interface SidebarProps {
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  currentPage: string
  setCurrentPage: (page: string) => void
}

export function Sidebar({ sidebarOpen, setSidebarOpen, currentPage, setCurrentPage }: SidebarProps) {
  return (
    <div
      className={`${sidebarOpen ? "w-64" : "w-20"} bg-white border-r border-gray-200 transition-all duration-300 flex flex-col`}
    >
      {/* Sidebar Header */}
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 flex items-center justify-center">
              <img src="/logo.png" className="w-8 h-8 object-contain" />
            </div>
            {sidebarOpen && (
              <div>
                <h2 className="font-semibold text-black-800">Agent Flow</h2>
              </div>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 text-gray-600 hover:bg-gray-100"
          >
            {sidebarOpen ? (
              <ChevronLeft className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </Button>
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
            <GitBranch className="w-6 h-6 flex-shrink-0" />
            {sidebarOpen && <span className="font-medium">그래프 에디터</span>}
          </button>

          <button
            onClick={() => setCurrentPage("agent-management")}
            className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
              currentPage === "agent-management"
                ? "bg-primary/5 text-primary border border-primary/20"
                : "text-gray-700 hover:bg-gray-50"
            }`}
          >
            <Bot className="w-6 h-6 flex-shrink-0" />
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
            <Database className="w-6 h-6 flex-shrink-0" />
            {sidebarOpen && <span className="font-medium">지식 관리</span>}
          </button>
        </nav>
      </div>
    </div>
  )
}
