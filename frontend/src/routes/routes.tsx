import {
  Navigate,
  RouterProvider,
  createBrowserRouter,
} from 'react-router-dom';

import { HomePage } from '@/pages/Home';

import { RouterPath } from './path';

const router = createBrowserRouter([
  {
    path: RouterPath.HOME,
    element: <HomePage />,
  },
  {
    path: RouterPath.CHAT_DETAIL,
    element: <HomePage />,
  },
  {
    path: RouterPath.NOT_FOUND,
    element: <Navigate to={RouterPath.HOME} />,
  },
]);

export const AppRouter = () => <RouterProvider router={router} />;
