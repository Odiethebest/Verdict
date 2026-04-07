import axios from 'axios'
import { ElMessage } from 'element-plus'

const client = axios.create({ baseURL: '/api' })

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail ?? error.message ?? 'Request failed'
    ElMessage({ type: 'error', message: String(detail) })
    return Promise.reject(error)
  },
)

export default client
