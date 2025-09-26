"use client"

import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Bell, Volume2, Menu } from "lucide-react"

interface HeaderProps {
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  currentPage: string
}

export function Header({ sidebarOpen, setSidebarOpen, currentPage }: HeaderProps) {
  return (
    <div className="bg-primary border-b border-primary/70 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 text-white hover:bg-primary/80"
          >
            <Menu className="w-5 h-5" />
          </Button>
          <h2 className="font-semibold text-white">
            {currentPage === "realtime" 
              ? "실시간 상담지원" 
              : currentPage === "agent-management"
              ? "AI Agent 관리"
              : currentPage === "knowledge-management"
              ? "지식 관리"
              : currentPage === "graph-editor"
              ? "AI Agent 그래프 에디터"
              : "상담 후처리 관리"}
          </h2>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm" className="p-2 text-white hover:bg-primary/80">
              <Bell className="w-4 h-4" />
            </Button>
            <div className="flex items-center space-x-2 ml-4">
              <Avatar className="w-6 h-6">
                <AvatarFallback className="text-xs bg-primary/80 text-white">Y</AvatarFallback>
              </Avatar>
              <div className="text-white">
                <p className="text-sm font-medium">Yangseung Lee</p>
                <p className="text-xs text-primary-foreground/60">온라인</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
