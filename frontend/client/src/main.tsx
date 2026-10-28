import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { PageWrapper } from '../pages/PageWrapper'

ReactDOM.createRoot(document.getElementById('root')!).render(
    <PageWrapper>
        <App />
    </PageWrapper>
)