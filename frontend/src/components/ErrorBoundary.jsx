import React from 'react'

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught unhandled error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary-fallback" role="alert">
          <div className="error-boundary-card">
            <h2>Something went wrong</h2>
            <p className="error-boundary-text">
              An unexpected UI error occurred: {this.state.error?.message || 'Unknown error'}
            </p>
            <button className="error-boundary-btn" onClick={this.handleReset}>
              Reload Application
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
