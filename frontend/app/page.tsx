"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { MainContent } from "@/components/main-content"

export default function KBAgentAssistant() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [currentPage, setCurrentPage] = useState("graph-editor")

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} currentPage={currentPage} setCurrentPage={setCurrentPage} />

      <div className="flex-1 flex flex-col">
        <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} currentPage={currentPage} />

        <MainContent currentPage={currentPage} />
      </div>
    </div>
  )
}
