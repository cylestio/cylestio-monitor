# Dashboard Integration

Cylestio Monitor provides a powerful visualization layer through our open-source dashboard. This guide will help you set up and integrate the dashboard with your monitoring data.

## Overview

The Cylestio Dashboard is a separate repository that provides:

- Real-time monitoring of your AI agents
- Security alerts and incident tracking
- Performance metrics and analytics
- Detailed event logs and debugging tools

## Installation

The dashboard is available as a separate repository. You can install it using the following steps:

```bash
# Clone the dashboard repository
git clone https://github.com/cylestio/cylestio-dashboard.git

# Navigate to the dashboard directory
cd cylestio-dashboard

# Install dependencies
npm install

# Start the development server
npm run dev
```

## Configuration

To connect the dashboard to your Cylestio Monitor instance, you'll need to configure the connection settings:

1. Create a `.env` file in the dashboard root directory
2. Add the following configuration:

```
CYLESTIO_DB_PATH=/path/to/your/cylestio/database.db
CYLESTIO_API_KEY=your_api_key_if_enabled
```

## Features

### Real-time Monitoring

The dashboard provides real-time monitoring of your AI agents, including:

- Active agent status
- Recent events and interactions
- Performance metrics
- Security alerts

### Security Alerts

The security alerts panel shows:

- Dangerous prompt attempts
- Suspicious activity
- Compliance violations
- Access control issues

### Performance Analytics

Track the performance of your AI agents with:

- Response time metrics
- Token usage and costs
- Error rates
- Usage patterns

### Event Logs

Detailed event logs help you debug issues:

- Complete conversation history
- Request and response details
- Error messages and stack traces
- System events

## Customization

The dashboard can be customized to fit your needs:

### Custom Themes

```javascript
// In your dashboard config.js
module.exports = {
  theme: {
    primary: '#3B82F6',
    secondary: '#10B981',
    background: '#F8FAFC',
    text: '#1E293B'
  }
}
```

### Custom Widgets

You can create custom widgets to display specific metrics:

```javascript
// Example custom widget
import { Widget } from 'cylestio-dashboard';

export const CustomMetricWidget = () => {
  return (
    <Widget title="Custom Metric">
      {/* Your custom widget content */}
    </Widget>
  );
};
```

## API Access

The dashboard exposes an API that you can use to access your monitoring data programmatically:

```bash
curl -X GET http://localhost:3000/api/events \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Troubleshooting

### Common Issues

- **Dashboard can't connect to database**: Ensure the database path in your `.env` file is correct and accessible.
- **No data showing**: Check that your agents are properly configured with Cylestio Monitor.
- **Authentication errors**: Verify your API key is correctly set in both the dashboard and your monitoring configuration.

## Next Steps

- Check out the [Dashboard Repository](https://github.com/cylestio/cylestio-dashboard) for more information
- View the [API Reference](../sdk-reference/overview.md) for details on the available endpoints
- Learn about [Security Features](security-features.md) to get the most out of your monitoring 