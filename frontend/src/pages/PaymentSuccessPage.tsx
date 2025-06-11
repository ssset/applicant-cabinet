import React from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle } from "lucide-react";
import { Link } from "react-router-dom";

const PaymentSuccessPage = () => {
    return (
        <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center py-12 px-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="w-full max-w-md"
            >
                <Card className="border-0 shadow-lg">
                    <CardHeader className="bg-appBlue text-white rounded-t-lg">
                        <CardTitle className="text-2xl text-center">Спасибо за оплату!</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-6 text-center">
                        <div className="flex justify-center mb-6">
                            <CheckCircle className="h-16 w-16 text-green-500" />
                        </div>
                        <p className="text-gray-700 mb-4">
                            Ваша оплата успешно обработана. Администратор свяжется с вами в ближайшее время для уточнения деталей.
                        </p>
                        <p className="text-gray-600 mb-6">
                            Мы отправили подтверждение на указанный вами email.
                        </p>
                        <Link to="/">
                            <Button className="bg-appBlue hover:bg-appBlue/90">
                                Вернуться на главную
                            </Button>
                        </Link>
                    </CardContent>
                </Card>
            </motion.div>
        </div>
    );
};

export default PaymentSuccessPage;