import { Link } from 'react-router-dom'

const Footer = () => {
  return (
    <footer className="bg-background border-t border-border px-6 py-4">
      <div className="flex flex-col sm:flex-row justify-between items-center space-y-2 sm:space-y-0">
        {/* Left Section - Copyright */}
        <div className="text-sm text-muted-foreground">
          © 2025 GrantThrive. All rights reserved.
        </div>

        {/* Center Section - Links */}
        <div className="flex items-center space-x-6 text-sm">
          <Link 
            to="/help" 
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            Help
          </Link>
          <Link 
            to="/privacy" 
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            Privacy
          </Link>
          <Link 
            to="/terms" 
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            Terms
          </Link>
          <Link 
            to="/support" 
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            Support
          </Link>
        </div>

        {/* Right Section - Version */}
        <div className="text-sm text-muted-foreground">
          Version 1.0.0
        </div>
      </div>
    </footer>
  )
}

export default Footer

