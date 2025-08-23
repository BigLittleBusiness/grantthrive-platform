import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '../../lib/utils'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { 
  LayoutDashboard, 
  FileText, 
  Users, 
  BarChart3, 
  MessageSquare, 
  Settings,
  ChevronLeft,
  ChevronRight,
  Plus,
  Search,
  Filter
} from 'lucide-react'

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  const navigation = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: LayoutDashboard,
      current: location.pathname === '/dashboard' || location.pathname === '/',
      badge: null
    },
    {
      name: 'Grants',
      href: '/grants',
      icon: FileText,
      current: location.pathname === '/grants',
      badge: '12'
    },
    {
      name: 'Applications',
      href: '/applications',
      icon: Users,
      current: location.pathname === '/applications',
      badge: '8'
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: BarChart3,
      current: location.pathname === '/analytics',
      badge: null
    },
    {
      name: 'Community',
      href: '/community',
      icon: MessageSquare,
      current: location.pathname === '/community',
      badge: '3'
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Settings,
      current: location.pathname === '/settings',
      badge: null
    }
  ]

  const quickActions = [
    { name: 'New Grant', icon: Plus, action: () => console.log('New Grant') },
    { name: 'Search', icon: Search, action: () => console.log('Search') },
    { name: 'Filter', icon: Filter, action: () => console.log('Filter') }
  ]

  return (
    <div className={cn(
      "bg-background border-r border-border flex flex-col transition-all duration-300",
      collapsed ? "w-16" : "w-64"
    )}>
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <h2 className="text-lg font-semibold text-foreground">Navigation</h2>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="h-8 w-8 p-0"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                item.current
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              )}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {!collapsed && (
                <>
                  <span className="flex-1">{item.name}</span>
                  {item.badge && (
                    <Badge variant="secondary" className="text-xs">
                      {item.badge}
                    </Badge>
                  )}
                </>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Quick Actions */}
      {!collapsed && (
        <div className="p-4 border-t border-border">
          <h3 className="text-sm font-medium text-muted-foreground mb-3">Quick Actions</h3>
          <div className="space-y-2">
            {quickActions.map((action) => {
              const Icon = action.icon
              return (
                <Button
                  key={action.name}
                  variant="outline"
                  size="sm"
                  onClick={action.action}
                  className="w-full justify-start"
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {action.name}
                </Button>
              )
            })}
          </div>
        </div>
      )}

      {/* Collapsed Quick Actions */}
      {collapsed && (
        <div className="p-2 border-t border-border">
          <div className="space-y-2">
            {quickActions.map((action) => {
              const Icon = action.icon
              return (
                <Button
                  key={action.name}
                  variant="outline"
                  size="sm"
                  onClick={action.action}
                  className="w-full h-8 p-0"
                >
                  <Icon className="h-4 w-4" />
                </Button>
              )
            })}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="p-4 border-t border-border">
        {!collapsed ? (
          <div className="text-xs text-muted-foreground">
            <p>GrantThrive v1.0</p>
            <p>© 2025 GrantThrive</p>
          </div>
        ) : (
          <div className="text-center">
            <div className="text-xs text-muted-foreground">GT</div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Sidebar

