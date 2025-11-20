# Backend Section - Data Storage and Elaboration

## Description

The Backend is composed of a FastAPI + PostgreSQL application, which is able to store data about zones, meters and misurations.

## Quick Start

### 🐳 Docker Image

```bash
# Pull Docker Image
docker pull ghcr.io/gizano/earthquake-data-server:1.0.0
```

#### 📦 Image URL: <a href="https://github.com/users/GiZano/packages/container/package/earthquake-data-server">Docker Image</a>


## Alert Algorithm

-- TO-DO

## Data Model

### Entities

<table>
    <thead>
        <tr>
            <th>Entity</th>
            <th>Attributes</th>
            <th>Relationships</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Zone</td>
            <td>
                <ul>
                    <li><u>id</u></li>
                    <li>city</li>
                </ul>
            </td>
            <td></td>
        </tr>
        <tr>
            <td>Misurator</td>
            <td>
                <ul>
                    <li><u>id</u></li>
                    <li>active</li>
                    <li><i>zone_id</i></li>
                </ul>
            </td>
            <td>zone_id --> Zone</td>
        </tr>
        <tr>
            <td>Misuration</td>
            <td>
                <ul>
                    <li><u>id</u></li>
                    <li>created_at</li>
                    <li>value</li>
                    <li><i>misurator_id</i></li>
                </ul>
            </td>
            <td>misurator_id --> Misurator</td>
        </tr>
    </tbody>
</table>

## API

You can find full APIs documentation here:

#### <a href="https://github.com/GiZano/Electro-Domestic-Earthquake-Alarm-System/tree/main/Backend%20-%20Data%20Elaborator/api"> API Docs</a>

You can also find it here, after starting the application:

#### localhost:8000/docs