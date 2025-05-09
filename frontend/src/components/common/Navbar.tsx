
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const Navbar = () => {
  const { isAuthenticated, signOut } = useAuth();

  return (
    <motion.header 
      className="bg-white shadow-sm py-4"
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="container mx-auto px-4 flex justify-between items-center">
        <Link to="/" className="text-2xl font-bold text-appBlue">
          Applicant Portal
        </Link>
        
        {isAuthenticated && (
          <Button 
            variant="ghost"
            onClick={signOut}
            className="hover:bg-red-50 hover:text-red-600 text-gray-700"
          >
            Выйти
          </Button>
        )}
      </div>
    </motion.header>
  );
};

export default Navbar;
