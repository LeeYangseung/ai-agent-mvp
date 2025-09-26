"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"

interface ResizerProps {
  onResize: (delta: number) => void
  className?: string
}

export function Resizer({ onResize, className = "" }: ResizerProps) {
  const [isResizing, setIsResizing] = useState(false)
  const startX = useRef(0)

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return

      const delta = e.clientX - startX.current
      onResize(delta)
      startX.current = e.clientX
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    if (isResizing) {
      document.addEventListener("mousemove", handleMouseMove)
      document.addEventListener("mouseup", handleMouseUp)
      document.body.style.cursor = "col-resize"
      document.body.style.userSelect = "none"
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
    }
  }, [isResizing, onResize])

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsResizing(true)
    startX.current = e.clientX
  }

  return (
    <div
      className={`w-1 bg-gray-200 hover:bg-primary/40 cursor-col-resize transition-colors duration-200 ${className}`}
      onMouseDown={handleMouseDown}
    >
      <div className="w-full h-full flex items-center justify-center">
        <div className="w-0.5 h-8 bg-gray-400 hover:bg-primary transition-colors duration-200"></div>
      </div>
    </div>
  )
}
