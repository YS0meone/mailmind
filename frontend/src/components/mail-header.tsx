"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ComposeDialog } from "@/components/compose-dialog";
import { Moon, Sun, Monitor, Plus, Settings, LogOut } from "lucide-react";

interface MailHeaderProps {
  isCollapsed: boolean;
  userEmail?: string;
  userName?: string;
}

export function MailHeader({
  isCollapsed,
  userEmail,
  userName,
}: MailHeaderProps) {
  const [theme, setTheme] = useState<"light" | "dark" | "system">("system");

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme") as
      | "light"
      | "dark"
      | "system";
    if (savedTheme) {
      setTheme(savedTheme);
      applyTheme(savedTheme);
    } else {
      // Initialize with system theme if no preference is saved
      applyTheme("system");
    }
  }, []);

  const applyTheme = (newTheme: "light" | "dark" | "system") => {
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);

    const root = window.document.documentElement;
    root.classList.remove("light", "dark");

    if (newTheme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
        .matches
        ? "dark"
        : "light";
      root.classList.add(systemTheme);
    } else {
      root.classList.add(newTheme);
    }
  };

  const getThemeIcon = () => {
    switch (theme) {
      case "light":
        return <Sun className="h-4 w-4" />;
      case "dark":
        return <Moon className="h-4 w-4" />;
      default:
        return <Monitor className="h-4 w-4" />;
    }
  };

  const getInitials = (name?: string, email?: string) => {
    if (name) {
      return name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2);
    }
    if (email) {
      return email.split("@")[0].slice(0, 2).toUpperCase();
    }
    return "U";
  };

  const getDisplayName = (email?: string) => {
    if (!email) return "User";
    // Extract username from email and capitalize
    const username = email.split("@")[0];
    return username.charAt(0).toUpperCase() + username.slice(1);
  };

  const displayName = userName || getDisplayName(userEmail);
  const displayEmail = userEmail || "user@example.com";

  if (isCollapsed) {
    return (
      <div className="flex items-center justify-center p-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-8 w-8 rounded-full">
              <Avatar className="h-8 w-8">
                <AvatarImage src="" alt={displayName} />
                <AvatarFallback className="text-xs">
                  {getInitials(userName, userEmail)}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end" forceMount>
            <div className="flex flex-col space-y-1 p-2">
              <p className="text-sm font-medium leading-none">{displayName}</p>
              <p className="text-xs leading-none text-muted-foreground">
                {displayEmail}
              </p>
            </div>
            <ComposeDialog
              trigger={
                <DropdownMenuItem>
                  <Plus className="mr-2 h-4 w-4" />
                  <span>Compose</span>
                </DropdownMenuItem>
              }
            />
            <DropdownMenuItem onClick={() => applyTheme("light")}>
              <Sun className="mr-2 h-4 w-4" />
              <span>Light</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => applyTheme("dark")}>
              <Moon className="mr-2 h-4 w-4" />
              <span>Dark</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => applyTheme("system")}>
              <Monitor className="mr-2 h-4 w-4" />
              <span>System</span>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="mr-2 h-4 w-4" />
              <span>Settings</span>
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={async () => {
                try {
                  const response = await fetch(
                    `${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/logout`,
                    {
                      method: "POST",
                      credentials: "include",
                    }
                  );
                  if (!response.ok) {
                    throw new Error("Logout failed");
                  }
                } catch (e) {
                  console.error(e);
                }
                // Force a hard redirect after cookie deletion
                window.location.replace("/login");
              }}
            >
              <LogOut className="mr-2 h-4 w-4" />
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between p-2 space-x-2">
      <div className="flex items-center space-x-2 flex-1 min-w-0">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <Avatar className="h-8 w-8 flex-shrink-0">
                <AvatarImage src="" alt={displayName} />
                <AvatarFallback className="text-xs">
                  {getInitials(userName, userEmail)}
                </AvatarFallback>
              </Avatar>
              <span className="sr-only">User menu</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            <DropdownMenuItem>
              <Settings className="mr-2 h-4 w-4" />
              <span>Settings</span>
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={async () => {
                try {
                  const response = await fetch(
                    `${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/logout`,
                    {
                      method: "POST",
                      credentials: "include",
                    }
                  );
                  if (!response.ok) {
                    throw new Error("Logout failed");
                  }
                } catch (e) {
                  console.error(e);
                }
                window.location.href = "/login";
              }}
            >
              <LogOut className="mr-2 h-4 w-4" />
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <div className="flex flex-col min-w-0 flex-1">
          <p className="text-sm font-medium leading-none truncate">
            {displayName}
          </p>
          <p className="text-xs leading-none text-muted-foreground truncate">
            {displayEmail}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-1 flex-shrink-0">
        <ComposeDialog
          trigger={
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <Plus className="h-4 w-4" />
              <span className="sr-only">Compose</span>
            </Button>
          }
        />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              {getThemeIcon()}
              <span className="sr-only">Toggle theme</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => applyTheme("light")}>
              <Sun className="mr-2 h-4 w-4" />
              <span>Light</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => applyTheme("dark")}>
              <Moon className="mr-2 h-4 w-4" />
              <span>Dark</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => applyTheme("system")}>
              <Monitor className="mr-2 h-4 w-4" />
              <span>System</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
