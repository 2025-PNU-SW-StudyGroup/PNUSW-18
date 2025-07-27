import axios from 'axios';

export const fetchInstance = axios.create({
  //baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

fetchInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    console.error('에러:', error);

    return Promise.reject(error);
  }
);

fetchInstance.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('에러:', error);

    return Promise.reject(
      error.response?.data || {
        message: '알 수 없는 오류가 발생했습니다.',
        status: 500,
      }
    );
  }
);
